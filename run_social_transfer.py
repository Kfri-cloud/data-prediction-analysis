from pathlib import Path
import json,csv,hashlib
from datetime import datetime,timezone
import numpy as np
from run_social import observations,feature,fit_prediction,bound
from run_pilot import block_interval
ROOT=Path(__file__).resolve().parent
MODELS=['N0','Trend','N1','Analog']
def candidates(data,origin,problem):
    fitted=fit_prediction(data,origin,problem)
    if fitted is None:return None
    train=[t for t in sorted(data) if t+1<=origin and t+1 in data and feature(data,t) is not None]
    x=np.array([feature(data,t) for t in train]);q=np.array(feature(data,origin));sd=x.std(0);mask=sd>1e-10
    d=np.sqrt(np.mean(((x[:,mask]-q[mask])/sd[mask])**2,axis=1)) if mask.any() else np.zeros(len(train))
    nearest=sorted(range(len(train)),key=lambda j:(d[j],train[j]))[:5];years=[train[j] for j in nearest]
    values={'N0':data[origin],'Trend':bound(data[origin]+(data[origin]-data[origin-3])/3,problem),'N1':fitted['prediction'],'Analog':bound(data[origin]+float(np.median([data[t+1]-data[t] for t in years])),problem)}
    return dict(predictions=values,neighbors=[dict(origin_year=train[j],target_year=train[j]+1,distance=float(d[j]),change=data[train[j]+1]-data[train[j]]) for j in nearest],training_n=len(train),latest_training_target=max(train)+1)
def select(history,origin):
    eligible=sorted([r for r in history if r['target_year']<=origin],key=lambda r:r['target_year'])[-8:]
    if len(eligible)<5:return 'N0',eligible
    return min(MODELS,key=lambda k:sum(abs(r['actual']-r[k]) for r in eligible)/len(eligible)),eligible
def summary(rows):
    errors={k:np.array([abs(r['actual']-r[k]) for r in rows]) for k in MODELS+['Selected']}
    mae={k:float(v.mean()) for k,v in errors.items()}
    return dict(n=len(rows),mae=mae,selected_improvement_pct=100*(1-mae['Selected']/mae['N0']) if mae['N0'] else None,descriptive_interval=block_interval(errors['N0']-errors['Selected'],2),selection_counts={k:sum(r['chosen']==k for r in rows) for k in MODELS})
def main():
    old=json.loads((ROOT/'results/social_lock.json').read_text())
    for f,h in old['sha256'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h,f
    files=['run_social_transfer.py','social_transfer_protocol.json','results/social_lock.json','results/social_baseline_predictions.csv']
    hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files};lock=ROOT/'results/social_transfer_lock.json'
    if lock.exists():assert json.loads(lock.read_text())['sha256']==hashes
    else:lock.write_text(json.dumps(dict(sha256=hashes,frozen_at=datetime.now(timezone.utc).isoformat()),indent=2))
    oldrows={(r['region'],r['problem'],int(r['target_year'])):r for r in csv.DictReader((ROOT/'results/social_baseline_predictions.csv').read_text().splitlines())}
    catalog=json.loads((ROOT/'social_catalog.json').read_text(encoding='utf8'));result=[];output=[];audit=[]
    for region,region_name in catalog['regions'].items():
        for p in catalog['problems']:
            r=dict(region=region,region_name=region_name,problem=p['id'],name=p['name'],target=p['target'],unit=p['unit'],issue=p['issue'],source=p['source'],projection_2026=None)
            path=ROOT/f'data/social/{region}/{p["id"]}.json'
            if not p['indicator'] or not path.exists():r['status']='NOT_EXECUTED_NO_HARMONIZED_SERIES';result.append(r);continue
            data=observations(json.loads(path.read_text()),region,p['indicator']);r.update(latest_year=max(data),latest_value=data[max(data)],observations=len(data));history=[];rows=[]
            for year in sorted(data):
                if year+1 not in data:continue
                c=candidates(data,year,p['id'])
                if c is None:continue
                chosen,validation=select(history,year)
                row=dict(region=region,problem=p['id'],origin_year=year,target_year=year+1,actual=data[year+1],**c['predictions'],Selected=c['predictions'][chosen],chosen=chosen,training_n=c['training_n'],latest_training_target=c['latest_training_target'],selection_n=len(validation),latest_selection_target=max((v['target_year'] for v in validation),default=0))
                history.append(row)
                if 2016<=year+1<=2025:
                    rows.append(row)
                    for n in c['neighbors']:audit.append(dict(region=region,problem=p['id'],forecast_origin=year,**n))
            if len(rows)<5:r.update(status='NOT_EXECUTED_INSUFFICIENT_EVALUATION',eligible_years=len(rows));result.append(r);continue
            for row in rows:
                previous=oldrows[(region,p['id'],row['target_year'])]
                assert abs(row['N0']-float(previous['N0']))<1e-10 and abs(row['N1']-float(previous['N1']))<1e-10
            r.update(status='RETROSPECTIVE_NUMERIC_ONLY',summary=summary(rows),first_target=rows[0]['target_year'],last_target=rows[-1]['target_year'])
            if max(data)==2025:
                c=candidates(data,2025,p['id']);chosen,validation=select(history,2025)
                r['projection_2026']=dict(value=c['predictions'][chosen],chosen=chosen,candidates=c['predictions'],selection_n=len(validation),latest_selection_target=max((v['target_year'] for v in validation),default=0),neighbors=c['neighbors'],label='CONDITIONAL_2026_ANNUAL_PROJECTION_NOT_REALTIME')
            output+=rows;result.append(r);print(region,p['id'],round(r['summary']['selected_improvement_pct'],2),r['projection_2026']['chosen'] if r['projection_2026'] else '-',flush=True)
    for name,records in [('social_transfer_predictions.csv',output),('social_transfer_neighbors.csv',audit)]:
        with (ROOT/'results'/name).open('w',encoding='utf8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    (ROOT/'results/social_transfer_results.json').write_text(json.dumps(dict(status='EXPLORATORY_CURRENT_VINTAGE_REPLAY',results=result),ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()

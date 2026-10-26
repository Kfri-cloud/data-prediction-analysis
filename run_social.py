from pathlib import Path
from datetime import datetime,timezone
import json,csv,hashlib
import numpy as np
from run_pilot import ridge
ROOT=Path(__file__).resolve().parent

def observations(payload,region,indicator):
    rows=payload[1];out={}
    for row in rows:
        if row['countryiso3code']!=region or row['indicator']['id']!=indicator:raise ValueError('Region or indicator mismatch')
        if row['value'] is None:continue
        year=int(row['date']);v=float(row['value'])
        if year in out or not np.isfinite(v):raise ValueError('Duplicate or nonfinite observation')
        out[year]=v
    return out

def feature(data,origin):
    if not all(origin-k in data for k in range(4)):return None
    return [data[origin],data[origin]-data[origin-1],data[origin]-data[origin-3]]

def fit_prediction(data,origin,problem):
    test=feature(data,origin)
    if test is None:return None
    train=[t for t in sorted(data) if t+1<=origin and t+1 in data and feature(data,t) is not None]
    if len(train)<10:return None
    X=np.array([feature(data,t) for t in train]);y=np.array([data[t+1]-data[t] for t in train])
    pred=data[origin]+ridge(X,y,np.array(test));pred=bound(pred,problem)
    return {'prediction':float(pred),'training_n':len(train),'latest_training_target_year':max(t+1 for t in train)}

def bound(value,problem):
    if problem!='living_cost':value=max(0.,value)
    if problem in ['youth_jobs','youth_neet']:value=min(100.,value)
    return value

def main():
    catalog=json.loads((ROOT/'social_catalog.json').read_text(encoding='utf8'));manifest=json.loads((ROOT/'results/social_sources.json').read_text())
    files=['social_protocol.json','social_catalog.json','run_social.py','run_pilot.py','results/social_sources.json']
    files += [f'data/social/{x["region"]}/{x["id"]}.json' for x in manifest if x['status']=='downloaded']
    hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
    lock=ROOT/'results/social_lock.json'
    if lock.exists():assert json.loads(lock.read_text())['sha256']==hashes,'Frozen social experiment changed'
    else:lock.write_text(json.dumps({'frozen_at_utc':datetime.now(timezone.utc).isoformat(),'sha256':hashes},indent=2))
    regions={};all_rows=[]
    for region in catalog['regions']:
        results=[]
        for p in catalog['problems']:
            common={'id':p['id'],'name':p['name'],'target':p['target'],'unit':p['unit'],'definition_issue':p['issue'],
                'final_50_50_status':'NOT_EXECUTED','missing_final_inputs':['domain-specific archived news and publication timestamps','historical numeric release vintages','validated contextual inputs and domain extractor'],
                'source':p['source'],'projection_2026':None}
            src=next((x for x in manifest if x['region']==region and x['id']==p['id']),None)
            if src is None or src['status']!='downloaded':
                common.update({'baseline_status':'NOT_EXECUTED_NO_HARMONIZED_SERIES','observations':0});results.append(common);continue
            path=ROOT/f'data/social/{region}/{p["id"]}.json'
            assert hashlib.sha256(path.read_bytes()).hexdigest()==src['sha256']
            data=observations(json.loads(path.read_text()),region,p['indicator'])
            common['observations']=len(data)
            if not data:common['baseline_status']='NOT_EXECUTED_NO_OBSERVATIONS';results.append(common);continue
            latest=max(data);common.update({'latest_year':latest,'latest_value':data[latest],'source_api':src['url']})
            rows=[]
            for target in range(2016,min(2025,latest)+1):
                if target not in data or target-1 not in data:continue
                fitted=fit_prediction(data,target-1,p['id'])
                if fitted is None:continue
                rows.append({'region':region,'problem':p['id'],'target_year':target,'origin_year':target-1,
                    'actual':data[target],'N0':data[target-1],'N1':fitted['prediction'],'training_n':fitted['training_n'],
                    'latest_training_target_year':fitted['latest_training_target_year']})
            if len(rows)<5:
                common.update({'baseline_status':'NOT_EXECUTED_INSUFFICIENT_EVALUATION','eligible_evaluation_years':len(rows)})
                results.append(common);continue
            e0=float(np.mean([abs(x['actual']-x['N0']) for x in rows]));e1=float(np.mean([abs(x['actual']-x['N1']) for x in rows]))
            common.update({'baseline_status':'RETROSPECTIVE_NUMERIC_DIAGNOSTIC_ONLY','evaluation_years':[x['target_year'] for x in rows],
                'n_evaluation':len(rows),'naive_mae':e0,'ridge_mae':e1,'relative_improvement_pct':100*(e0-e1)/e0 if e0 else None})
            if latest==2025:
                fitted=fit_prediction(data,2025,p['id'])
                if fitted:common['projection_2026']={'N0':data[2025],'N1':fitted['prediction'],
                    'label':'CONDITIONAL_NUMERIC_EXTRAPOLATION_NOT_FINAL_METHOD','training_n':fitted['training_n']}
            else:common['current_forecast_block_reason']='SOURCE_ENDPOINT_BEFORE_2025_NO_CURRENT_EXTRAPOLATION'
            all_rows+=rows;results.append(common)
        regions[region]={'region_name':catalog['regions'][region],'problems':results,
            'final_method_executed':0,'numeric_baselines_executed':sum(x['baseline_status']=='RETROSPECTIVE_NUMERIC_DIAGNOSTIC_ONLY' for x in results),
            'conditional_2026_numeric_extrapolations':sum(x['projection_2026'] is not None for x in results)}
        (ROOT/f'results/social_{region}.json').write_text(json.dumps(regions[region],ensure_ascii=False,indent=2),encoding='utf8')
    with (ROOT/'results/social_baseline_predictions.csv').open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(all_rows[0]));w.writeheader();w.writerows(all_rows)
    result={'status':'FINAL_METHOD_NOT_EXECUTED_DATA_GATES_UNMET','region_training_pooled':False,'regions':regions}
    (ROOT/'results/social_results.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    for k,r in regions.items():
        print(k,'final',r['final_method_executed'],'baselines',r['numeric_baselines_executed'],'projections',r['conditional_2026_numeric_extrapolations'])
        for p in r['problems']:print(p['id'],p['baseline_status'],p.get('relative_improvement_pct'),p.get('projection_2026'))
if __name__=='__main__':main()

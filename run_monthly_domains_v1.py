from pathlib import Path
from datetime import datetime,timezone
import csv,json,hashlib
import numpy as np
from fetch_monthly_domains import CATALOG
from run_pilot import ridge,block_interval
ROOT=Path(__file__).resolve().parent
MODELS=['Last','Seasonal','Drift','Ridge','Analog']
def load_series(path,key):
    raw=list(csv.DictReader(path.read_text(encoding='utf-8-sig').splitlines()));datekey=list(raw[0])[0]
    rows=[r for r in raw if '2000-01-01'<=r[datekey]<='2025-12-31']
    dates=[r[datekey] for r in rows];expected=[f'{year}-{month:02}-01' for year in range(2000,2026) for month in range(1,13)]
    assert dates==expected,'Missing, duplicate or nonmonthly dates'
    y=np.array([float(r[key]) for r in rows]);assert np.isfinite(y).all()
    return dates,y
def feature(y,i):
    month=i%12+1
    return np.array([y[i],y[i]-y[i-1],y[i]-y[i-3],y[i]-y[i-12],np.std(np.diff(y[i-12:i+1])),np.sin(month*2*np.pi/12),np.cos(month*2*np.pi/12)])
def predict(y,i,key):
    train=list(range(12,i))
    if len(train)<60:return None
    x=np.stack([feature(y,j) for j in train]);q=feature(y,i);delta=np.array([y[j+1]-y[j] for j in train]);sd=x.std(0);mask=sd>1e-10
    distance=np.mean(((x[:,mask]-q[mask])/sd[mask])**2,axis=1) if mask.any() else np.zeros(len(train))
    selected=np.argsort(distance,kind='stable')[:5]
    values=dict(Last=y[i],Seasonal=y[i-11],Drift=y[i]+(y[i]-y[i-12])/12,Ridge=y[i]+ridge(x,delta,q),Analog=y[i]+np.median(delta[selected]))
    return {k:float(min(100,max(0,v)) if key=='UNRATE' else max(0,v)) for k,v in values.items()}
def choose(history,origin):
    valid=[r for r in history if r['target_month']<=origin][-24:]
    return (min(MODELS,key=lambda k:np.mean([abs(r['actual']-r[k]) for r in valid])) if len(valid)>=12 else 'Last'),valid
def summarize(rows,ci=True):
    errors={k:np.array([abs(r['actual']-r[k]) for r in rows]) for k in MODELS+['Selected']};mae={k:float(v.mean()) for k,v in errors.items()}
    return dict(n=len(rows),mae=mae,improvement={b:100*(1-mae['Selected']/mae[b]) for b in ['Last','Seasonal']},intervals={b:block_interval(errors[b]-errors['Selected'],6) for b in ['Last','Seasonal']} if ci else {},selection_counts={k:sum(r['chosen']==k for r in rows) for k in MODELS})
def main():
    files=['run_monthly_domains.py','monthly_domains_protocol.json','fetch_monthly_domains.py','run_pilot.py','results/monthly_domains_sources.json']+[f'data/monthly_domains/{k}.csv' for k,_,_,_ in CATALOG]
    hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files};lock=ROOT/'results/monthly_domains_lock.json'
    if lock.exists():assert json.loads(lock.read_text())['sha256']==hashes
    else:lock.write_text(json.dumps(dict(sha256=hashes,frozen_at=datetime.now(timezone.utc).isoformat()),indent=2))
    results=[];allrows=[]
    for key,field,name,unit in CATALOG:
        dates,y=load_series(ROOT/f'data/monthly_domains/{key}.csv',key);history=[];rows=[]
        for i in range(12,len(y)-1):
            p=predict(y,i,key)
            if p is None:continue
            chosen,valid=choose(history,dates[i])
            row=dict(id=key,origin_month=dates[i],target_month=dates[i+1],actual=float(y[i+1]),**p,Selected=p[chosen],chosen=chosen,training_n=i-12,latest_train_target=dates[i],selection_n=len(valid),latest_selection_target=valid[-1]['target_month'] if valid else '')
            history.append(row)
            if dates[i+1]>='2016-01-01':rows.append(row)
        assert len(rows)==120
        s=summarize(rows);halves={name:summarize([r for r in rows if lo<=r['target_month']<hi],False) for name,lo,hi in [('2016-2020','2016-01-01','2021-01-01'),('2021-2025','2021-01-01','2026-01-01')]}
        passed=all(s['improvement'][b]>=10 and s['intervals'][b][0]>0 and all(h['improvement'][b]>0 for h in halves.values()) for b in ['Last','Seasonal'])
        results.append(dict(id=key,field=field,name=name,unit=unit,source=f'https://fred.stlouisfed.org/series/{key}',summary=s,halves=halves,screen_pass=bool(passed),best_posthoc=min(s['mae'],key=s['mae'].get)))
        allrows+=rows;print(key,s['improvement'],passed,flush=True)
    with (ROOT/'results/monthly_domains_predictions.csv').open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(allrows[0]));w.writeheader();w.writerows(allrows)
    (ROOT/'results/monthly_domains_results.json').write_text(json.dumps(dict(status='CURRENT_VINTAGE_EXPLORATORY_NOT_REALTIME',results=results),ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()

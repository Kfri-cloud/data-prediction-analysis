from pathlib import Path
from datetime import datetime,timezone
import json,csv,hashlib
import numpy as np
from fetch_diverse import CATALOG
from run_diverse import features,target,text_features
from run_events import clauses
from run_pilot import event_text,eligible_train,block_interval
from run_market import NAMES,load_bars,at_origin,cutoff_for
ROOT=Path(__file__).resolve().parent
def distances(blocks,train,i):
    total=np.zeros(len(train));active=0
    for x in blocks:
        sd=x[train].std(0);mask=sd>1e-10
        if mask.any():
            total+=np.mean(((x[train][:,mask]-x[i,mask])/sd[mask])**2,axis=1);active+=1
    return np.sqrt(total/max(active,1))
def neighbors(samples,train,dist,k=5):
    chosen=[]
    for pos in sorted(range(len(train)),key=lambda p:(dist[p],train[p])):
        j=train[pos];start=samples[j]['date'];end=max(samples[j]['future_time']['timestamp'])[:10]
        if all(end<samples[t]['date'] or start>max(samples[t]['future_time']['timestamp'])[:10] for t,_ in chosen):
            chosen.append((j,float(dist[pos])))
            if len(chosen)==k:break
    return chosen
def naive(s,kind):
    return 0. if kind=='price' else float(np.mean(s['past_time']['value'][-52:-40])-s['past_time']['value'][-1])
def summarize(rows,ci=True):
    keys=['Naive','B1','History','Raw5','Analog5','News5','Analog3']
    y=np.array([r['actual'] for r in rows]);err={k:np.abs(y-[r[k] for r in rows]) for k in keys};m={k:float(v.mean()) for k,v in err.items()}
    return dict(n=len(rows),mae=m,improvement={k:100*(1-m['Analog5']/m[k]) if m[k]>0 else None for k in ['Naive','B1','History']},interval=block_interval(err['Naive']-err['Analog5']) if ci else None,news_improvement_pct=100*(1-m['News5']/m['Analog5']) if m['Analog5']>0 else None)
def main():
    previous=json.loads((ROOT/'results/diverse_lock.json').read_text())
    for f,h in previous['sha256'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h,f
    files=['run_analogue.py','analogue_protocol.json','results/diverse_predictions.csv','results/diverse_lock.json']
    hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files};lock=ROOT/'results/analogue_lock.json'
    if lock.exists():assert json.loads(lock.read_text())['sha256']==hashes
    else:lock.write_text(json.dumps(dict(sha256=hashes,frozen_at=datetime.now(timezone.utc).isoformat()),indent=2))
    prior=list(csv.DictReader((ROOT/'results/diverse_predictions.csv').read_text().splitlines()))
    dictionary=json.loads((ROOT/'keyword_dictionary.json').read_text())
    dictionary.update(technology=['artificial intelligence','robot','robots','robotics','cybersecurity','data breach','software'],leisure=['travel','tourism','flight','flights','festival','festivals','esports','concert'],shopping=['shopping','discount','discounts','school','air conditioner','black friday'],supply=['supply','production','harvest','crop','crops','drought','weather'])
    bars={n:load_bars(ROOT/f'data/market/{n}.json') for n in NAMES};results=[];output=[];audit=[]
    for key,field,name,kind,_ in CATALOG:
        ss=sorted(json.loads((ROOT/f'data/diverse/{key}.json').read_text(encoding='utf8'))['samples'],key=lambda s:s['date']);lookup={s['date']:i for i,s in enumerate(ss)}
        x=np.stack([features(s) for s in ss]);market=np.array([sum([at_origin(bars[n],cutoff_for(s['date']))[0] for n in NAMES],[]) for s in ss]);news=np.stack([text_features(clauses(event_text(s)),dictionary) for s in ss])
        blocks=[x[:,:10],x[:,10:12],x[:,12:],market];y=np.array([target(s,kind) for s in ss]);b=np.array([naive(s,kind) for s in ss]);residual=y-b;rows=[]
        for old in [r for r in prior if r['indicator']==key]:
            i=lookup[old['date']];train=eligible_train(ss,old['date']);assert abs(y[i]-float(old['actual']))<1e-9 and abs(b[i]-float(old['Naive']))<1e-9
            d=distances(blocks,train,i);dn=distances(blocks+[news],train,i);sets={'Analog5':neighbors(ss,train,d,5),'News5':neighbors(ss,train,dn,5),'Analog3':neighbors(ss,train,d,3)}
            row=dict(indicator=key,date=old['date'],target_end=old['target_end'],actual=float(y[i]),Naive=float(b[i]),B1=float(old['B1']),History=float(b[i]+np.median(residual[train])))
            for model,chosen in sets.items():
                ids=[j for j,_ in chosen];row[model]=float(b[i]+np.median(residual[ids])) if len(ids)>=3 else float(b[i])
                for rank,(j,distance) in enumerate(chosen,1):audit.append(dict(indicator=key,origin=old['date'],model=model,rank=rank,neighbor_origin=ss[j]['date'],neighbor_end=max(ss[j]['future_time']['timestamp'])[:10],distance=distance,actual=float(y[j]),naive=float(b[j]),residual=float(residual[j])))
            ids=[j for j,_ in sets['Analog5']];vals=residual[ids]
            row['Raw5']=float(np.median(y[ids])) if len(ids)>=3 else float(b[i]);row['neighbor_n']=len(ids);row['fallback']=len(ids)<3;row['median_distance']=float(np.median([v for _,v in sets['Analog5']]))
            row['case_q25']=float(b[i]+np.quantile(vals,.25));row['case_q75']=float(b[i]+np.quantile(vals,.75));row['residual_sign_agreement']=float(max(np.sum(vals>0),np.sum(vals<0),np.sum(vals==0))/len(vals));rows.append(row)
        independent=[];end=''
        for r in rows:
            if r['date']>end:independent.append(r);end=r['target_end']
        result=dict(id=key,field=field,name=name,kind=kind,summary=summarize(rows),nonoverlap=summarize(independent),years={yr:summarize([r for r in rows if r['date'].startswith(yr)],False) for yr in sorted({r['date'][:4] for r in rows})},latest=rows[-1],fallbacks=sum(r['fallback'] for r in rows),latest_neighbors=[r for r in audit if r['indicator']==key and r['origin']==rows[-1]['date'] and r['model']=='Analog5'])
        results.append(result);output+=rows;print(key,round(result['summary']['improvement']['Naive'],2),flush=True)
    for file,records in [('analogue_predictions.csv',output),('analogue_neighbors.csv',audit)]:
        with (ROOT/'results'/file).open('w',encoding='utf8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    (ROOT/'results/analogue_results.json').write_text(json.dumps(dict(status='EXPLORATORY_ANALOGUES_NOT_VALIDATED',results=results),ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()

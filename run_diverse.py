from pathlib import Path
from datetime import date,datetime,timezone
import json,csv,re,hashlib
import numpy as np
from fetch_diverse import CATALOG
from run_pilot import eligible_train,ridge,event_text,block_interval
from run_keywords import keyword_features
from run_events import clauses,structured_features,MODAL,NEGATION,ABOVE,BELOW
from run_weighted import OUTCOME,choose_weight
from run_market import NAMES,load_bars,at_origin,cutoff_for
ROOT=Path(__file__).resolve().parent
GROUPS=['psyche','outcome','surprise','unknown']
PSYCHE=r'\b(?:fear|fears|feared|anxiety|optimism|pessimism|sentiment|confidence|concern|concerns|worried|worries|enthusiasm|excitement|panic|uncertainty|hopes|hopeful|anticipation)\b'
def classify(text):
    out={g:[] for g in GROUPS}
    for clause in clauses(text):
        s=' '.join(re.findall('[a-z]+',clause.lower()))
        mood=bool(re.search(PSYCHE,s));fact=bool(re.search(OUTCOME,s));future=bool(re.search(MODAL,s));neg=bool(re.search(NEGATION,s))
        if not future and not neg and bool(re.search(ABOVE,s))!=bool(re.search(BELOW,s)):g='surprise'
        elif mood and not fact and not neg:g='psyche'
        elif fact and not mood and not future and not neg:g='outcome'
        else:g='unknown'
        out[g].append(clause)
    return out
def category_weights(counts,alpha,reverse=False):
    priority=np.array([1,alpha,alpha,1] if reverse else [alpha,1,alpha,1],float)
    w=np.sqrt(np.minimum(np.asarray(counts,float),10))*priority
    return w/w.sum() if w.sum() else np.zeros(4)
def blend(pred,counts,alpha,base,reverse=False):
    w=category_weights(counts,alpha,reverse)
    return float(w@pred) if w.sum() else float(base)
def features(s):
    p=np.array(s['past_time']['value'],float);scale=max(float(np.mean(np.abs(p))),1e-6)
    d=date.fromisoformat(s['date']);x=[(p[-1]-p[-1-k])/scale for k in [1,5,12,24,48,95]]
    x += [float(np.std(np.diff(p)[-k:])/scale) for k in [12,48]]
    x += [p[-1]/scale,float(np.mean(p[-12:])/scale),np.sin(2*np.pi*d.month/12),np.cos(2*np.pi*d.month/12)]
    matches=re.findall(r'max=([-\d.]+).*?min=([-\d.]+).*?mean=([-\d.]+), median=([-\d.]+), trend=(\w+)',s['covariates_info'])
    if not matches:raise ValueError('No numeric covariates')
    for a,b,c,e,t in matches:x+=list(map(float,[a,b,c,e]))+[{'upward':1,'downward':-1,'stable':0,'flat':0}[t]]
    return np.array(x)
def text_features(parts,dictionary):
    text='; '.join(parts)
    return np.r_[keyword_features(text,dictionary),len(parts),structured_features(text,dictionary)[0][:len(dictionary)]]
def target(s,kind):
    last=float(s['past_time']['value'][-1]);future=float(np.mean(s['future_time']['value']))
    if kind=='price':
        assert last>0
        return 100*(future/last-1)
    return future-last
def summary(rows,interval=True):
    keys=['Naive','B1','Original50','Equal','Psyche','Reverse','IndexOnly','NewsOnly']
    y=np.array([r['actual'] for r in rows]);err={k:np.abs(y-[r[k] for r in rows]) for k in keys};mae={k:float(v.mean()) for k,v in err.items()}
    return dict(n=len(rows),mae=mae,improvement={k:100*(1-mae['Psyche']/mae[k]) if mae[k]>0 else None for k in ['Naive','B1','Original50','Equal','Reverse']},interval=block_interval(err['Equal']-err['Psyche']) if interval else None,direction_hits=int(sum(np.sign(y)==np.sign([r['Psyche'] for r in rows]))))
def main():
    deps=['run_diverse.py','diverse_protocol.json','fetch_diverse.py','run_pilot.py','run_keywords.py','run_events.py','run_weighted.py','run_market.py','keyword_dictionary.json','results/diverse_sources.json']+[f'data/diverse/{x[0]}.json' for x in CATALOG]+[f'data/market/{n}.json' for n in NAMES]
    hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in deps};lock=ROOT/'results/diverse_lock.json'
    if lock.exists():assert json.loads(lock.read_text())['sha256']==hashes
    else:lock.write_text(json.dumps(dict(sha256=hashes,frozen_at=datetime.now(timezone.utc).isoformat()),indent=2))
    dictionary=json.loads((ROOT/'keyword_dictionary.json').read_text())
    dictionary.update(technology=['artificial intelligence','robot','robots','robotics','cybersecurity','data breach','software'],leisure=['travel','tourism','flight','flights','festival','festivals','esports','concert'],shopping=['shopping','discount','discounts','school','air conditioner','black friday'],supply=['supply','production','harvest','crop','crops','drought','weather'])
    bars={n:load_bars(ROOT/f'data/market/{n}.json') for n in NAMES};results=[];output=[];audit=[]
    for key,field,name,kind,_ in CATALOG:
        ss=sorted(json.loads((ROOT/f'data/diverse/{key}.json').read_text(encoding='utf8'))['samples'],key=lambda s:s['date'])
        assert len({s['date'] for s in ss})==len(ss)
        for s in ss:
            assert len(s['past_time']['value'])==96 and len(s['future_time']['value'])==12
            for k in ['past_time','future_time']:
                assert len(s[k]['timestamp'])==len(s[k]['value']) and s[k]['timestamp']==sorted(set(s[k]['timestamp'])) and np.isfinite(s[k]['value']).all()
            assert max(s['past_time']['timestamp'])<min(s['future_time']['timestamp']) and min(s['future_time']['timestamp'])[:10]==s['date']
        base=np.stack([features(s) for s in ss]);parts=[classify(event_text(s)) for s in ss];counts=np.array([[len(p[g]) for g in GROUPS] for p in parts])
        market=np.array([sum([at_origin(bars[n],cutoff_for(s['date']))[0] for n in NAMES],[]) for s in ss])
        arms={'B1':base,'Nasdaq':np.column_stack([base,market[:,4:8]]),'Others':np.column_stack([base,market[:,:4],market[:,8:]]),'M':np.column_stack([base,market]),'AllNews':np.column_stack([base,np.stack([text_features(clauses(event_text(s)),dictionary) for s in ss])])}
        arms.update({g:np.column_stack([base,np.stack([text_features(p[g],dictionary) for p in parts])]) for g in GROUPS})
        y=np.array([target(s,kind) for s in ss]);oof={}
        for i,s in enumerate(ss):
            train=eligible_train(ss,s['date'])
            if len(train)>=8:oof[i]={k:ridge(x[train],y[train],x[i]) for k,x in arms.items()}
            for g in GROUPS:
                audit += [dict(indicator=key,date=s['date'],category=g,clause_sha256=hashlib.sha256(c.encode()).hexdigest()) for c in parts[i][g]]
        rows=[]
        for i,s in enumerate(ss):
            train=eligible_train(ss,s['date'])
            if len(train)<16 or not '2024-01-01'<=s['date']<'2026-04-01':continue
            eligible=[j for j in train if j in oof]
            iw=choose_weight(np.array([oof[j]['Nasdaq'] for j in eligible]),np.array([oof[j]['Others'] for j in eligible]),y[eligible],False)
            def error(a):return np.mean([abs(y[j]-blend(np.array([oof[j][g] for g in GROUPS]),counts[j],a,oof[j]['B1'])) for j in eligible])
            alpha=min([2.,3.],key=error) if len(eligible)>=8 else 2.
            p=oof[i];index=iw*p['Nasdaq']+(1-iw)*p['Others'];gp=np.array([p[g] for g in GROUPS]);news=blend(gp,counts[i],alpha,p['B1']);equal=blend(gp,counts[i],1,p['B1']);reverse=blend(gp,counts[i],alpha,p['B1'],True)
            naive=0. if kind=='price' else float(np.mean(s['past_time']['value'][-52:-40])-s['past_time']['value'][-1])
            row=dict(indicator=key,date=s['date'],target_end=max(s['future_time']['timestamp'])[:10],training_n=len(train),latest_train_target=max(max(ss[j]['future_time']['timestamp']) for j in train),weight_validation_n=len(eligible),weight_latest_target=max((max(ss[j]['future_time']['timestamp']) for j in eligible),default=''),actual=float(y[i]),Naive=naive,B1=p['B1'],Original50=.5*(p['M']+p['AllNews']),Equal=.5*(index+equal),Psyche=.5*(index+news),Reverse=.5*(index+reverse),IndexOnly=.5*(index+p['AllNews']),NewsOnly=.5*(p['M']+news),index_prediction=index,news_prediction=news,nasdaq_weight=iw,alpha=alpha)
            row.update({g+'_weight':float(w) for g,w in zip(GROUPS,category_weights(counts[i],alpha))});row.update({g+'_clauses':int(n) for g,n in zip(GROUPS,counts[i])});rows.append(row)
        independent=[];end=''
        for r in rows:
            if r['date']>end:independent.append(r);end=r['target_end']
        r=dict(id=key,field=field,name=name,kind=kind,samples=len(ss),first=rows[0]['date'],last=rows[-1]['date'],unit='변화율 pp' if kind=='price' else '검색지수 점',summary=summary(rows),nonoverlap=summary(independent),years={yr:summary([r for r in rows if r['date'].startswith(yr)],False) for yr in sorted({r['date'][:4] for r in rows})},category_counts={g:int(counts[:,j].sum()) for j,g in enumerate(GROUPS)},latest=rows[-1],validity='EXPLORATORY_ONLY')
        results.append(r);output+=rows;print(key,len(rows),len(independent),round(r['summary']['improvement']['Equal'],3),flush=True)
    for name,records in [('diverse_predictions.csv',output),('diverse_classification.csv',audit)]:
        with (ROOT/'results'/name).open('w',encoding='utf8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    (ROOT/'results/diverse_results.json').write_text(json.dumps(dict(status='EXPLORATORY_PROXY_NOT_CAUSAL',results=results),ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()

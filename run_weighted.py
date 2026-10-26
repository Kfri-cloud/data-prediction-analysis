from pathlib import Path
import json,csv,re,hashlib
from datetime import datetime,timezone
import numpy as np
from run_pilot import base_features,event_text,eligible_train,ridge,block_interval
from run_keywords import keyword_features
from run_events import clauses,structured_features,MODAL,NEGATION
from run_market import NAMES,load_bars,at_origin,cutoff_for
from fetch_indicators import CATALOG
ROOT=Path(__file__).resolve().parent
OUTCOME=r'\b(?:reported|released|announced|approved|enacted|implemented|rose|fell|increased|decreased|reached|recorded|posted|produced|exported|imported|cut|raised)\b'
def split_news(text):
    result=[];other=[]
    for clause in clauses(text):
        normalized=' '.join(re.findall('[a-z]+',clause.lower()))
        good=bool(re.search(OUTCOME,normalized)) and not re.search(MODAL,normalized) and not re.search(NEGATION,normalized)
        (result if good else other).append(clause)
    return result,other
def news_features(parts,dictionary):
    text='; '.join(parts)
    return np.r_[keyword_features(text,dictionary),len(parts),structured_features(text,dictionary)[0][:8]]
def choose_weight(a,b,y,focused):
    if len(y)<8:return .5
    grid=[.5,.75,1.] if focused else [.5,.25,.75,0.,1.]
    return min(grid,key=lambda w:float(np.mean(np.abs(y-(w*a+(1-w)*b)))))
def summary(rows):
    keys=['B1','M','Sdir','Cavg','Windex','Wnews','Weighted','Unconstrained','IndexOnly','NewsOnly']
    y=np.array([r['actual'] for r in rows]);errors={k:np.abs(y-[r[k] for r in rows]) for k in keys}
    mae={k:float(v.mean()) for k,v in errors.items()}
    return dict(n=len(rows),mae=mae,improvement_old_pct=100*(1-mae['Weighted']/mae['Cavg']),improvement_B1_pct=100*(1-mae['Weighted']/mae['B1']),delta_interval=block_interval(errors['Cavg']-errors['Weighted']))
def main():
    oldlock=json.loads((ROOT/'results/indicator_lock.json').read_text())
    for f,h in oldlock['sha256'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h,f
    files=['run_weighted.py','weighted_protocol.json','results/indicator_predictions.csv','results/indicator_lock.json']
    hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files};lock=ROOT/'results/weighted_lock.json'
    if lock.exists():assert json.loads(lock.read_text())['sha256']==hashes
    else:lock.write_text(json.dumps(dict(sha256=hashes,frozen_at=datetime.now(timezone.utc).isoformat()),indent=2))
    prior=list(csv.DictReader((ROOT/'results/indicator_predictions.csv').read_text().splitlines()))
    dictionary=json.loads((ROOT/'keyword_dictionary.json').read_text());bars={n:load_bars(ROOT/f'data/market/{n}.json') for n in NAMES}
    results=[];output=[]
    for key,name,_ in CATALOG:
        ss=sorted(json.loads((ROOT/f'data/indicators/{key}.json').read_text(encoding='utf8'))['samples'],key=lambda s:s['date'])
        base=np.stack([base_features(s) for s in ss]);market=np.array([sum([at_origin(bars[n],cutoff_for(s['date']))[0] for n in NAMES],[]) for s in ss])
        parts=[split_news(event_text(s)) for s in ss]
        arms={'Nasdaq':np.column_stack([base,market[:,4:8]]),'OtherIndices':np.column_stack([base,market[:,:4],market[:,8:]]),'Outcomes':np.column_stack([base,np.stack([news_features(p[0],dictionary) for p in parts])]),'OtherNews':np.column_stack([base,np.stack([news_features(p[1],dictionary) for p in parts])])}
        y=np.array([100*(np.mean(s['future_time']['value'])/s['past_time']['value'][-1]-1) for s in ss]);oof={};lookup={s['date']:i for i,s in enumerate(ss)}
        for i,s in enumerate(ss):
            train=eligible_train(ss,s['date'])
            if len(train)>=8:oof[i]={k:ridge(x[train],y[train],x[i]) for k,x in arms.items()}
        rows=[]
        for old in [r for r in prior if r['indicator']==key]:
            i=lookup[old['date']];eligible=[j for j in eligible_train(ss,old['date']) if j in oof]
            w={}
            for focused,suffix in [(True,''),(False,'_free')]:
                for label,a,b in [('nasdaq','Nasdaq','OtherIndices'),('outcome','Outcomes','OtherNews')]:
                    w[label+suffix]=choose_weight(np.array([oof[j][a] for j in eligible]),np.array([oof[j][b] for j in eligible]),y[eligible],focused)
            p=oof[i];ix=w['nasdaq']*p['Nasdaq']+(1-w['nasdaq'])*p['OtherIndices'];nw=w['outcome']*p['Outcomes']+(1-w['outcome'])*p['OtherNews']
            free=.5*(w['nasdaq_free']*p['Nasdaq']+(1-w['nasdaq_free'])*p['OtherIndices'])+.5*(w['outcome_free']*p['Outcomes']+(1-w['outcome_free'])*p['OtherNews'])
            row={k:old[k] for k in ['indicator','date','target_end','training_n','latest_train_target']}
            row.update({k:float(old[k]) for k in ['actual','B1','M','Sdir','Cavg']})
            row.update(w);row.update(p);row.update(weight_validation_n=len(eligible),weight_latest_target=max((max(ss[j]['future_time']['timestamp']) for j in eligible),default=''),Windex=ix,Wnews=nw,Weighted=.5*(ix+nw),Unconstrained=free,IndexOnly=.5*(ix+float(old['Sdir'])),NewsOnly=.5*(float(old['M'])+nw),outcome_clauses=len(parts[i][0]),other_clauses=len(parts[i][1]))
            rows.append(row)
        result=dict(id=key,name=name,summary=summary(rows),years={yr:summary([r for r in rows if r['date'].startswith(yr)]) for yr in sorted({r['date'][:4] for r in rows})},mean_weights={k:float(np.mean([r[k] for r in rows])) for k in w},latest=rows[-1],outcome_clauses=sum(len(p[0]) for p in parts),total_clauses=sum(len(p[0])+len(p[1]) for p in parts))
        results.append(result);output+=rows;print(key,round(result['summary']['improvement_old_pct'],3),flush=True)
    with (ROOT/'results/weighted_predictions.csv').open('w',encoding='utf8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=list(output[0]));writer.writeheader();writer.writerows(output)
    (ROOT/'results/weighted_results.json').write_text(json.dumps(dict(status='POST_HOC_EXPLORATORY_NOT_VALIDATED',results=results),ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()

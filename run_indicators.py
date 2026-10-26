"""Unretuned transfer of the FX candidate to ten separate commodity targets."""
from pathlib import Path
import csv,json,hashlib
from datetime import datetime,timezone
import numpy as np
from fetch_indicators import CATALOG
from run_pilot import base_features,event_text,eligible_train,ridge,block_interval
from run_keywords import keyword_features
from run_events import structured_features
from run_market import load_bars,at_origin,cutoff_for,NAMES
ROOT=Path(__file__).resolve().parent
KEYS=['B0','B1','M','Sdir','Cavg']
def validate(samples):
    assert len({s['date'] for s in samples})==len(samples)
    for s in samples:
        for key,n in [('past_time',96),('future_time',12)]:
            v=s[key];assert len(v['value'])==len(v['timestamp'])==n
            assert v['timestamp']==sorted(set(v['timestamp']))
            assert np.isfinite(v['value']).all() and min(v['value'])>0
        assert max(s['past_time']['timestamp'])<min(s['future_time']['timestamp'])
        assert min(s['future_time']['timestamp'])[:10]==s['date']
def summarize(rows,ci=True):
    y=np.array([r['actual'] for r in rows])
    errors={k:np.abs(y-np.array([r[k] for r in rows])) for k in KEYS}
    mae={k:float(v.mean()) for k,v in errors.items()}
    return dict(n=len(rows),mae_pp=mae,improvement_pct=100*(1-mae['Cavg']/mae['B1']),
        versus_M_pct=100*(1-mae['Cavg']/mae['M']),versus_Sdir_pct=100*(1-mae['Cavg']/mae['Sdir']),
        direction_hits=int(sum(np.sign(y)==np.sign([r['Cavg'] for r in rows]))),
        paired_delta_pp=float((errors['B1']-errors['Cavg']).mean()),
        descriptive_interval_pp=block_interval(errors['B1']-errors['Cavg']) if ci else None)
def main():
    files=['run_indicators.py','indicator_protocol.json','fetch_indicators.py','run_pilot.py','run_events.py','run_keywords.py','run_market.py','keyword_dictionary.json','results/indicator_sources.json']+[f'data/indicators/{k}.json' for k,_,_ in CATALOG]+[f'data/market/{k}.json' for k in NAMES]
    hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
    lock=ROOT/'results/indicator_lock.json'
    if lock.exists():assert json.loads(lock.read_text())['sha256']==hashes,'Frozen inputs changed'
    else:lock.write_text(json.dumps(dict(frozen_at=datetime.now(timezone.utc).isoformat(),sha256=hashes),indent=2))
    dictionary=json.loads((ROOT/'keyword_dictionary.json').read_text())
    bars={n:load_bars(ROOT/f'data/market/{n}.json') for n in NAMES}
    results=[];allrows=[]
    for key,name,_ in CATALOG:
        data=json.loads((ROOT/f'data/indicators/{key}.json').read_text(encoding='utf8'))
        ss=sorted(data['samples'],key=lambda s:s['date']);validate(ss)
        base=np.stack([base_features(s) for s in ss])
        news=np.stack([np.r_[keyword_features(event_text(s),dictionary),s['metadata']['event_count'],structured_features(event_text(s),dictionary)[0][:8]] for s in ss])
        market=np.array([sum([at_origin(bars[n],cutoff_for(s['date']))[0] for n in NAMES],[]) for s in ss])
        arms={'B1':base,'M':np.column_stack([base,market]),'Sdir':np.column_stack([base,news])}
        y=np.array([100*(np.mean(s['future_time']['value'])/s['past_time']['value'][-1]-1) for s in ss]);rows=[]
        for i,s in enumerate(ss):
            train=eligible_train(ss,s['date'])
            if not '2024-01-01'<=s['date']<'2026-04-01' or len(train)<16:continue
            row=dict(indicator=key,date=s['date'],target_end=max(s['future_time']['timestamp'])[:10],training_n=len(train),latest_train_target=max(max(ss[t]['future_time']['timestamp']) for t in train),actual=float(y[i]),B0=0.)
            row.update({k:ridge(x[train],y[train],x[i]) for k,x in arms.items()})
            row['Cavg']=.5*row['M']+.5*row['Sdir'];rows.append(row)
        assert len(rows)>=12
        summary=summarize(rows)
        years={yr:summarize([r for r in rows if r['date'].startswith(yr)],False) for yr in sorted({r['date'][:4] for r in rows})}
        screen=summary['improvement_pct']>=5 and summary['descriptive_interval_pp'][0]>0 and all(years.get(yr,{}).get('improvement_pct',-1)>0 for yr in ['2024','2025'])
        results.append(dict(id=key,name=name,samples=len(ss),first=rows[0]['date'],last=rows[-1]['date'],summary=summary,years=years,numerical_screen_pass=bool(screen),provenance_verified=False,validity='EXPLORATORY_NOT_VALIDATED',latest_replay=rows[-1]))
        allrows+=rows
        print(name,len(rows),round(summary['improvement_pct'],3),summary['descriptive_interval_pp'],flush=True)
    with (ROOT/'results/indicator_predictions.csv').open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(allrows[0]));w.writeheader();w.writerows(allrows)
    (ROOT/'results/indicator_results.json').write_text(json.dumps(dict(status='EXPLORATORY_TRANSFER_NOT_LIVE',results=results),ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()

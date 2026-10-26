from pathlib import Path
from datetime import datetime,timezone,timedelta
import csv,json,hashlib
import numpy as np
from run_pilot import base_features,event_text,eligible_train,ridge,block_interval
from run_keywords import keyword_features

ROOT=Path(__file__).resolve().parent
NAMES=['sp500','nasdaq100','kospi','kosdaq']

def load_bars(path):
    r=json.loads(path.read_text())['chart']['result'][0]
    bars=[(int(t),float(v)) for t,v in zip(r['timestamp'],r['indicators']['quote'][0]['close']) if v is not None]
    assert len({t for t,v in bars})==len(bars)
    assert all(np.isfinite(v) and v>0 for t,v in bars)
    return sorted(bars)

def at_origin(bars,cutoff):
    selected=[(t,v) for t,v in bars if t+48*3600<=cutoff]
    if len(selected)<21:raise ValueError('Insufficient historical index observations')
    if cutoff-selected[-1][0]>14*86400:raise ValueError('Stale index history')
    p=np.array([v for t,v in selected[-21:]])
    features=[100*(p[-1]/p[-1-k]-1) for k in [1,5,20]]
    features.append(float(np.std(100*np.diff(p)/p[:-1])))
    return features,selected[-1][0]

def cutoff_for(date):
    return datetime.fromisoformat(date).replace(tzinfo=timezone(timedelta(hours=9))).timestamp()

def summary(rows):
    y=np.array([r['actual'] for r in rows]);keys=['B1','M','K1','MK']
    errors={k:np.abs(y-np.array([r[k] for r in rows])) for k in keys}
    mae={k:float(v.mean()) for k,v in errors.items()}
    return {'n':len(rows),'mae_pp':mae,
        'index_improvement_pct':100*(mae['B1']-mae['M'])/mae['B1'],
        'news_given_indices_improvement_pct':100*(mae['M']-mae['MK'])/mae['M'],
        'primary_delta_pp':float((errors['M']-errors['MK']).mean()),
        'primary_descriptive_ci_pp':block_interval(errors['M']-errors['MK']),
        'index_descriptive_ci_pp':block_interval(errors['B1']-errors['M']),
        'direction_accuracy':{k:float(np.mean(np.sign(y)==np.sign([r[k] for r in rows]))) for k in keys}}

def main():
    files=['market_protocol.json','run_market.py','run_keywords.py','run_pilot.py','keyword_dictionary.json',
           'data/timesx_krw.json','results/keyword_predictions.csv']+[f'data/market/{n}.json' for n in NAMES]
    hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
    lock=ROOT/'results/market_lock.json'
    if lock.exists():assert json.loads(lock.read_text())['sha256']==hashes,'Frozen market experiment changed'
    else:lock.write_text(json.dumps({'frozen_at_utc':datetime.now(timezone.utc).isoformat(),'prior_results_seen':True,'sha256':hashes},indent=2))
    dictionary=json.loads((ROOT/'keyword_dictionary.json').read_text())
    ss=sorted(json.loads((ROOT/'data/timesx_krw.json').read_text(encoding='utf8'))['samples'],key=lambda s:s['date'])
    bars={n:load_bars(ROOT/f'data/market/{n}.json') for n in NAMES}
    source=json.loads((ROOT/'results/market_sources.json').read_text())
    for src in source:assert src['sha256']==hashes[f'data/market/{src["name"]}.json']
    base=np.stack([base_features(s) for s in ss])
    kw=np.column_stack([np.stack([keyword_features(event_text(s),dictionary) for s in ss]),[s['metadata']['event_count'] for s in ss]])
    market=[];audit=[]
    for s in ss:
        cutoff=cutoff_for(s['date']);x=[]
        for n in NAMES:
            feat,t=at_origin(bars[n],cutoff);x+=feat
            audit.append({'origin':s['date'],'index':n,'cutoff_utc':datetime.fromtimestamp(cutoff,timezone.utc).isoformat(),
                'latest_bar_timestamp_utc':datetime.fromtimestamp(t,timezone.utc).isoformat(),'lag_hours':(cutoff-t)/3600})
        market.append(x)
    market=np.array(market);arms={'M':np.column_stack([base,market]),'MK':np.column_stack([base,market,kw])}
    y=np.array([100*(np.mean(s['future_time']['value'])/s['past_time']['value'][-1]-1) for s in ss])
    old=list(csv.DictReader((ROOT/'results/keyword_predictions.csv').open(encoding='utf8')));lookup={s['date']:i for i,s in enumerate(ss)}
    rows=[]
    for o in old:
        i=lookup[o['date']];train=eligible_train(ss,o['date'])
        assert len(train)==int(o['training_n']) and abs(y[i]-float(o['actual']))<1e-10
        assert abs(ridge(base[train],y[train],base[i])-float(o['B1']))<1e-10
        k=np.column_stack([base,kw]);assert abs(ridge(k[train],y[train],k[i])-float(o['K1']))<1e-10
        row={k:o[k] for k in ['date','block','training_n','latest_train_target']}
        row.update({k:float(o[k]) for k in ['actual','B1','K1']})
        row.update({k:ridge(X[train],y[train],X[i]) for k,X in arms.items()});rows.append(row)
    for file,records in [('market_predictions.csv',rows),('market_alignment.csv',audit)]:
        with (ROOT/'results'/file).open('w',encoding='utf8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    now=datetime.now(timezone.utc);current=[]
    for n in NAMES:
        latest=bars[n][-1][0]
        try:
            feat,t=at_origin(bars[n],now.timestamp());status='eligible_under_48h_convention'
        except ValueError:
            feat=None;t=None;status='stale_or_insufficient_do_not_use_live'
        current.append({'index':n,'latest_observed_timestamp_utc':datetime.fromtimestamp(latest,timezone.utc).isoformat(),
            'eligible_latest_timestamp_utc':datetime.fromtimestamp(t,timezone.utc).isoformat() if t else None,
            'lagged_returns_1_5_20_and_volatility_pct':feat,'status':status})
    result={'status':'POST_HOC_EXPLORATORY_NOT_VALIDATED','all':summary(rows),
        'blocks':{b:summary([r for r in rows if r['block']==b]) for b in ['development','confirmation','latest_holdout']},
        'current_snapshot_asof_utc':now.isoformat(),'current_snapshot':current,
        'alignment_rows':len(audit),'minimum_lag_hours':min(r['lag_hours'] for r in audit),
        'source_provenance_verified':False,'new_untouched_holdout':False,'investor_flow_used':False,'current_fx_prediction_issued':False}
    (ROOT/'results/market_results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':main()

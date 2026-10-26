from pathlib import Path
from datetime import datetime,timezone
import csv,json,hashlib
import numpy as np
from run_pilot import base_features,event_text,eligible_train,ridge,block_interval
from run_keywords import keyword_features
from run_events import structured_features
from run_market import load_bars,at_origin,cutoff_for,NAMES
ROOT=Path(__file__).resolve().parent
KEYS=['B0','B1','M','Sdir','Cavg','Cjoint','Cslim']

def average(a,b):return .5*a+.5*b

def paired_sources(market,events):
    m={r['date']:r for r in market};e={r['date']:r for r in events}
    if len(m)!=len(market) or len(e)!=len(events) or set(m)!=set(e):raise ValueError('Origin mismatch or duplicates')
    for d in sorted(m):
        for k in ['actual','B1']:
            if abs(float(m[d][k])-float(e[d][k]))>1e-10:raise ValueError('Different target or baseline')
        for k in ['training_n','block','latest_train_target']:
            if m[d][k]!=e[d][k]:raise ValueError('Training/evaluation mismatch')
    return [(m[d],e[d]) for d in sorted(m)]

def summarize(rows):
    y=np.array([r['actual'] for r in rows]);err={k:np.abs(y-np.array([r[k] for r in rows])) for k in KEYS}
    mae={k:float(v.mean()) for k,v in err.items()}
    return {'n':len(rows),'mae_pp':mae,'improvement_vs_numeric_pct':{k:100*(mae['B1']-mae[k])/mae['B1'] for k in KEYS},
        'direction_hits':{k:int(np.sum(np.sign(y)==np.sign([r[k] for r in rows]))) for k in KEYS if k!='B0'},
        'primary_descriptive_ci_pp':{k:block_interval(err[k]-err['Cavg']) for k in ['B1','M','Sdir']},
        'primary_paired_delta_pp':{k:float((err[k]-err['Cavg']).mean()) for k in ['B1','M','Sdir']}}

def main():
    # Verify earlier frozen source data and implementations before composing their predictions.
    for name in ['event_lock.json','market_lock.json']:
        lock=json.loads((ROOT/'results'/name).read_text())
        for f,h in lock['sha256'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h,f
    files=['combination_protocol.json','run_combinations.py','results/event_predictions.csv','results/market_predictions.csv',
           'run_events.py','run_market.py','run_keywords.py','run_pilot.py','keyword_dictionary.json','data/timesx_krw.json']+[f'data/market/{n}.json' for n in NAMES]
    hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files};path=ROOT/'results/combination_lock.json'
    if path.exists():assert json.loads(path.read_text())['sha256']==hashes,'Frozen combination changed'
    else:path.write_text(json.dumps({'frozen_at_utc':datetime.now(timezone.utc).isoformat(),'prior_results_used_for_selection':True,'sha256':hashes},indent=2))
    dictionary=json.loads((ROOT/'keyword_dictionary.json').read_text())
    ss=sorted(json.loads((ROOT/'data/timesx_krw.json').read_text(encoding='utf8'))['samples'],key=lambda s:s['date'])
    base=np.stack([base_features(s) for s in ss]);kw=np.column_stack([np.stack([keyword_features(event_text(s),dictionary) for s in ss]),[s['metadata']['event_count'] for s in ss]])
    directions=np.stack([structured_features(event_text(s),dictionary)[0][:8] for s in ss])
    bars={n:load_bars(ROOT/f'data/market/{n}.json') for n in NAMES};market=[]
    for s in ss:
        x=[]
        for n in NAMES:x+=at_origin(bars[n],cutoff_for(s['date']))[0]
        market.append(x)
    market=np.array(market);M=np.column_stack([base,market]);S=np.column_stack([base,kw,directions])
    arms={'Cjoint':np.column_stack([base,market,kw,directions]),'Cslim':np.column_stack([base,market,directions])}
    pairs=paired_sources(list(csv.DictReader((ROOT/'results/market_predictions.csv').open())),list(csv.DictReader((ROOT/'results/event_predictions.csv').open())))
    lookup={s['date']:i for i,s in enumerate(ss)};y=np.array([100*(np.mean(s['future_time']['value'])/s['past_time']['value'][-1]-1) for s in ss]);rows=[]
    for m,e in pairs:
        i=lookup[m['date']];train=eligible_train(ss,m['date'])
        assert len(train)==int(m['training_n']) and abs(y[i]-float(m['actual']))<1e-10
        assert abs(ridge(M[train],y[train],M[i])-float(m['M']))<1e-10
        assert abs(ridge(S[train],y[train],S[i])-float(e['Sdir']))<1e-10
        row={k:m[k] for k in ['date','block','training_n','latest_train_target']}
        row.update({'actual':float(m['actual']),'B0':0.,'B1':float(m['B1']),'M':float(m['M']),'Sdir':float(e['Sdir'])})
        row['Cavg']=average(row['M'],row['Sdir']);row.update({k:ridge(X[train],y[train],X[i]) for k,X in arms.items()});rows.append(row)
    with (ROOT/'results/combination_predictions.csv').open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    result={'status':'POST_SELECTION_EXPLORATORY_NOT_VALIDATED','all':summarize(rows),
        'blocks':{b:summarize([r for r in rows if r['block']==b]) for b in ['development','confirmation','latest_holdout']},
        'component_prediction_correlation':float(np.corrcoef([r['M'] for r in rows],[r['Sdir'] for r in rows])[0,1]),
        'primary':'Cavg','candidates_frozen_before_this_run':True,'selected_using_prior_outcomes':True,
        'new_untouched_holdout':False,'source_provenance_verified':False,'current_forecast_issued':False}
    (ROOT/'results/combination_results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
if __name__=='__main__':main()

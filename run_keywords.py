"""Post-hoc keyword comparison; does not reuse the word 'holdout' as a new claim."""
from pathlib import Path
from datetime import datetime, timezone
import csv, hashlib, json, re
import numpy as np
from run_pilot import base_features, event_text, eligible_train, ridge, block_interval

ROOT=Path(__file__).resolve().parent

def keyword_features(text, dictionary):
    words=re.findall(r'[a-z]+',text.lower())
    normalized=' '.join(words)
    counts=[]
    for terms in dictionary.values():
        alternatives=sorted(terms,key=lambda t:(-len(t.split()),-len(t),t))
        pattern=r'\b(?:'+'|'.join(re.escape(t) for t in alternatives)+r')\b'
        counts.append(len(re.findall(pattern,normalized)))
    return np.array(counts,dtype=float)*1000/max(1,len(words))

def summary(rows):
    y=np.array([r['actual'] for r in rows])
    errors={k:np.abs(y-np.array([r[k] for r in rows])) for k in ['B0','B1','B2','B3','K1','KS']}
    mae={k:float(v.mean()) for k,v in errors.items()}
    return {'n':len(rows),'mae_pp':mae,
        'keyword_mae_improvement_pct':100*(mae['B1']-mae['K1'])/mae['B1'],
        'keyword_vs_count_improvement_pct':100*(mae['B3']-mae['K1'])/mae['B3'],
        'paired_delta_pp':float(np.mean(errors['B1']-errors['K1'])),
        'descriptive_block_ci_pp':block_interval(errors['B1']-errors['K1']),
        'direction_accuracy':{k:float(np.mean(np.sign(y)==np.sign([r[k] for r in rows]))) for k in errors}}

def main():
    files=['keyword_protocol.json','keyword_dictionary.json','run_keywords.py','run_pilot.py','data/timesx_krw.json','results/pilot_predictions.csv']
    hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
    lock=ROOT/'results/keyword_lock.json'
    if lock.exists():
        assert json.loads(lock.read_text())['sha256']==hashes,'Frozen keyword experiment changed'
    else:
        lock.write_text(json.dumps({'frozen_at_utc':datetime.now(timezone.utc).isoformat(),'prior_pilot_results_already_seen':True,'sha256':hashes},indent=2))
    dictionary=json.loads((ROOT/'keyword_dictionary.json').read_text())
    samples=sorted(json.loads((ROOT/'data/timesx_krw.json').read_text(encoding='utf8'))['samples'],key=lambda s:s['date'])
    base=np.stack([base_features(s) for s in samples])
    kw=np.stack([keyword_features(event_text(s),dictionary) for s in samples])
    count=np.array([s['metadata']['event_count'] for s in samples])[:,None]
    extra=np.column_stack([kw,count])
    stale=np.vstack([np.zeros((1,extra.shape[1])),extra[:-1]])
    arms={'K1':np.column_stack([base,extra]),'KS':np.column_stack([base,stale])}
    y=np.array([100*(np.mean(s['future_time']['value'])/s['past_time']['value'][-1]-1) for s in samples])
    previous=list(csv.DictReader((ROOT/'results/pilot_predictions.csv').open(encoding='utf8')))
    lookup={s['date']:i for i,s in enumerate(samples)}
    rows=[]
    for old in previous:
        i=lookup[old['date']]; train=eligible_train(samples,old['date'])
        assert len(train)==int(old['training_n'])
        assert abs(float(old['actual'])-y[i])<1e-10
        assert abs(float(old['B1'])-ridge(base[train],y[train],base[i]))<1e-10
        row={k:old[k] for k in ['date','block','training_n','latest_train_target']}
        row.update({k:float(old[k]) for k in ['actual','B0','B1','B2','B3']})
        row.update({k:ridge(X[train],y[train],X[i]) for k,X in arms.items()})
        rows.append(row)
    with (ROOT/'results/keyword_predictions.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    # Only rates, not copyrighted source text, are included in the audit export.
    with (ROOT/'results/keyword_features.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.writer(f);w.writerow(['date',*dictionary,'event_count'])
        for s,features,c in zip(samples,kw,count):w.writerow([s['date'],*features,int(c[0])])
    result={'status':'POST_HOC_EXPLORATORY_NOT_VALIDATED','all':summary(rows),
        'blocks':{b:summary([r for r in rows if r['block']==b]) for b in ['development','confirmation','latest_holdout']},
        'source_provenance_verified':False,'new_untouched_holdout':False,
        'full_context_model_evaluated':False,'dictionary_topics':list(dictionary)}
    (ROOT/'results/keyword_results.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()

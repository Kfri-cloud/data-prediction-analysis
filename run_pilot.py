"""Exploratory, non-causal replay. Never upgrades provenance to verified."""
from pathlib import Path
import csv, hashlib, json, re
from datetime import date, datetime, timezone
import numpy as np

ROOT = Path(__file__).resolve().parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def event_text(sample):
    # Forecast calendar dates are already supplied equally to all arms.
    return re.sub(r'^.*?Recent related events.*?:\s*', '', sample['scenario'], count=1, flags=re.S)

def text_features(text):
    x = np.zeros(32)
    for token in re.findall(r'[a-z]{3,}', text.lower()):
        h = hashlib.sha256(token.encode()).digest()
        x[int.from_bytes(h[:4], 'big') % 32] += 1 if h[4] % 2 else -1
    return x / max(np.linalg.norm(x), 1.)

def base_features(s):
    p = np.asarray(s['past_time']['value'], float)
    d = date.fromisoformat(s['date'])
    x = [100 * (p[-1] / p[-1-k] - 1) for k in [1,5,12,24,48,95]]
    ret = 100 * np.diff(p) / p[:-1]
    x += [float(np.std(ret[-k:])) for k in [12,48]]
    x += [np.sin(d.month * 2*np.pi/12), np.cos(d.month*2*np.pi/12), d.weekday()]
    matches = re.findall(r'max=([-\d.]+).*?min=([-\d.]+).*?mean=([-\d.]+), median=([-\d.]+), trend=(\w+)', s['covariates_info'])
    if len(matches) != 9:
        raise ValueError('Unexpected covariate schema at ' + s['date'])
    for maximum, minimum, mean, median, trend in matches:
        x += list(map(float, [maximum, minimum, mean, median])) + [{'upward':1, 'downward':-1, 'stable':0, 'flat':0}.get(trend, 0)]
    x += [len(re.findall(r'\d{4}-\d{2}-\d{2}:', s['holiday_info']))]
    return np.array(x)

def eligible_train(samples, origin):
    return [i for i,s in enumerate(samples) if s['date'] < origin and max(s['future_time']['timestamp'])[:10] < origin]

def ridge(X, y, test):
    mu, sd = X.mean(0), X.std(0)
    sd[sd < 1e-10] = 1
    Z = (X-mu)/sd
    center = y.mean()
    # Mean-loss ridge, lambda=1, so the matrix penalty is n.
    beta = np.linalg.solve(Z.T@Z + len(y)*np.eye(Z.shape[1]), Z.T@(y-center))
    return float(center + ((test-mu)/sd)@beta)

def block_interval(delta, length=3):
    n = len(delta)
    if n < 2:
        return None
    rng = np.random.default_rng(20261026)
    length = min(length,n)
    means = []
    for _ in range(5000):
        starts = rng.integers(0,n-length+1,size=int(np.ceil(n/length)))
        ix = np.concatenate([np.arange(s,s+length) for s in starts])[:n]
        means.append(np.mean(delta[ix]))
    return [float(v) for v in np.quantile(means,[.025,.975])]

def summarize(rows):
    y = np.array([r['actual'] for r in rows])
    errors = {k: np.abs(y-np.array([r[k] for r in rows])) for k in ['B0','B1','B2','B3','B4']}
    maes = {k:float(e.mean()) for k,e in errors.items()}
    delta = errors['B1']-errors['B2']
    return {'n_origins':len(rows), 'first':rows[0]['date'], 'last':rows[-1]['date'], 'mae_pp':maes,
            'rmse_pp':{k:float(np.sqrt(np.mean((y-np.array([r[k] for r in rows]))**2))) for k in errors},
            'direction_accuracy':{k:float(np.mean(np.sign(y)==np.sign([r[k] for r in rows]))) for k in errors},
            'news_relative_mae_improvement_pct':100*(maes['B1']-maes['B2'])/maes['B1'],
            'paired_mae_difference_pp':float(delta.mean()), 'exploratory_95pct_block_ci_pp':block_interval(delta),
            'too_few_for_confirmation':len(rows)<12}

def main():
    out = ROOT/'results'
    lockpath = out/'pilot_lock.json'
    lock = {'protocol_sha256':digest(ROOT/'pilot_protocol.json'), 'data_sha256':digest(ROOT/'data/timesx_krw.json'),
            'implementation_sha256':digest(Path(__file__)), 'repository_commit':(ROOT/'data/timesx_commit.txt').read_text().strip()}
    if lockpath.exists():
        old = json.loads(lockpath.read_text())
        if any(old[k]!=v for k,v in lock.items()):
            raise RuntimeError('Frozen experiment changed; do not silently re-tune after results')
    else:
        lockpath.write_text(json.dumps({**lock,'frozen_at_utc':datetime.now(timezone.utc).isoformat()},indent=2))
    data = json.loads((ROOT/'data/timesx_krw.json').read_text(encoding='utf8'))
    ss = sorted(data['samples'],key=lambda s:s['date'])
    assert len({s['date'] for s in ss})==len(ss)
    for s in ss:
        assert len(s['past_time']['value'])==96 and len(s['future_time']['value'])==12
        assert max(s['past_time']['timestamp']) < min(s['future_time']['timestamp'])
        assert min(s['future_time']['timestamp'])[:10] == s['date']
        assert all(np.isfinite(s[k]['value']).all() for k in ['past_time','future_time'])
    base = np.stack([base_features(s) for s in ss])
    texts = np.stack([text_features(event_text(s)) for s in ss])
    counts = np.array([s['metadata']['event_count'] for s in ss])[:,None]
    stale = np.vstack([np.zeros((1,33)),np.column_stack([texts,counts])[:-1]])
    arms = {'B1':base,'B2':np.column_stack([base,texts,counts]),'B3':np.column_stack([base,counts]),'B4':np.column_stack([base,stale])}
    y = np.array([100*(np.mean(s['future_time']['value'])/s['past_time']['value'][-1]-1) for s in ss])
    rows=[]
    for i,s in enumerate(ss):
        if not '2024-01-01' <= s['date'] < '2026-04-01': continue
        train=eligible_train(ss,s['date'])
        if len(train)<16: continue
        block='development' if s['date']<'2025-01-01' else 'confirmation' if s['date']<'2026-01-01' else 'latest_holdout'
        row={'date':s['date'],'block':block,'training_n':len(train),'latest_train_target':max(max(ss[t]['future_time']['timestamp']) for t in train),'actual':float(y[i]),'B0':0.}
        row.update({k:ridge(X[train],y[train],X[i]) for k,X in arms.items()})
        rows.append(row)
    with (out/'pilot_predictions.csv').open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)
    alltext=json.dumps(data)
    audit={'sample_count':len(ss),'first_origin':ss[0]['date'],'last_origin':ss[-1]['date'],
           'explicit_source_urls_in_export':len(re.findall(r'https?://',alltext)),
           'publication_timestamp_field_present':'published_at' in alltext,
           'historical_snapshot_verified':False,'numeric_release_vintages_verified':False,
           'schema_and_window_order_checks':'passed','point_in_time_gate':'NOT_VERIFIED'}
    results={'status':'EXPLORATORY_ONLY_PROVENANCE_GATE_FAILED','data_audit':audit,'frozen_inputs':lock,
             'all_evaluated':summarize(rows),'blocks':{b:summarize([r for r in rows if r['block']==b]) for b in ['development','confirmation','latest_holdout']},
             'interpretation':'Neither positive nor negative results establish Seoul sales predictability or the general value of news. This fixed small ridge baseline tests exported retrospective event summaries only. No calibrated probabilities or causal claim.'}
    (out/'pilot_results.json').write_text(json.dumps(results,indent=2),encoding='utf8')
    print(json.dumps(results,indent=2))

if __name__=='__main__': main()

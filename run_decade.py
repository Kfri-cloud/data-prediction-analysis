from pathlib import Path
from datetime import datetime,timezone
import csv,json,hashlib
import numpy as np
from run_market import load_bars,at_origin,cutoff_for,NAMES
from run_pilot import ridge,block_interval
ROOT=Path(__file__).resolve().parent

def train_indices(samples,cutoff):
    return [j for j,s in enumerate(samples) if s['label_available']<=cutoff and s['cutoff']<cutoff]

def summary(rows):
    if not rows:return {'n':0}
    y=np.array([r['actual'] for r in rows]);keys=['D0','D1','DM']
    e={k:np.abs(y-np.array([r[k] for r in rows])) for k in keys};m={k:float(v.mean()) for k,v in e.items()}
    return {'n':len(rows),'mae_pp':m,'index_improvement_pct':100*(m['D1']-m['DM'])/m['D1'],
        'versus_naive_improvement_pct':100*(m['D0']-m['DM'])/m['D0'],
        'paired_delta_pp':float((e['D1']-e['DM']).mean()),'descriptive_ci_pp':block_interval(e['D1']-e['DM']),
        'direction_accuracy':{k:float(np.mean(np.sign(y)==np.sign([r[k] for r in rows]))) for k in ['D1','DM']}}

def main():
    files=['decade_protocol.json','run_decade.py','run_market.py','run_pilot.py']+[f'data/decade/{n}.json' for n in NAMES+['usdkrw']]
    hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
    lock=ROOT/'results/decade_lock.json'
    if lock.exists():assert json.loads(lock.read_text())['sha256']==hashes,'Frozen decade experiment changed'
    else:lock.write_text(json.dumps({'frozen_at_utc':datetime.now(timezone.utc).isoformat(),'sha256':hashes},indent=2))
    bars={n:load_bars(ROOT/f'data/decade/{n}.json') for n in NAMES+['usdkrw']}
    fx=bars['usdkrw'];start=next(i for i,(t,v) in enumerate(fx) if datetime.fromtimestamp(t,timezone.utc).year>=2012)
    samples=[];excluded=[];now=datetime.now(timezone.utc).timestamp()
    for i in range(start,len(fx)-11,12):
        date=datetime.fromtimestamp(fx[i][0],timezone.utc).date().isoformat();cutoff=cutoff_for(date)
        end=fx[i+11][0];enddate=datetime.fromtimestamp(end,timezone.utc).date().isoformat()
        if end+48*3600>now:continue
        try:
            fxt,t=at_origin(fx,cutoff);last=next(v for time,v in fx if time==t)
            d=datetime.fromisoformat(date);base=fxt+[np.sin(d.month*2*np.pi/12),np.cos(d.month*2*np.pi/12)]
            extra=[];lag=[]
            for n in NAMES:
                feat,ts=at_origin(bars[n],cutoff);extra+=feat;lag.append((cutoff-ts)/3600)
        except ValueError as err:
            excluded.append({'date':date,'reason':str(err)});continue
        assert fx[i][0]>=cutoff and t+48*3600<=cutoff
        y=100*(np.mean([v for t,v in fx[i:i+12]])/last-1)
        samples.append({'date':date,'target_end':enddate,'cutoff':cutoff,'label_available':end+48*3600,
            'base':base,'market':base+extra,'actual':float(y),'min_index_lag_hours':min(lag)})
    X=np.array([s['base'] for s in samples]);M=np.array([s['market'] for s in samples]);y=np.array([s['actual'] for s in samples]);rows=[];boundary=[]
    for i,s in enumerate(samples):
        if s['date']<'2016-01-01':continue
        if s['date']<'2026-01-01' and s['target_end']>='2026-01-01':boundary.append(s['date']);continue
        train=train_indices(samples,s['cutoff'])
        if len(train)<40:excluded.append({'date':s['date'],'reason':'under_40_training_samples'});continue
        row={k:s[k] for k in ['date','target_end','actual','min_index_lag_hours']}
        row.update({'year':int(s['date'][:4]),'training_n':len(train),'latest_train_available_utc':datetime.fromtimestamp(max(samples[j]['label_available'] for j in train),timezone.utc).isoformat(),
            'D0':0.,'D1':ridge(X[train],y[train],X[i]),'DM':ridge(M[train],y[train],M[i])});rows.append(row)
    ten=[r for r in rows if r['year']<=2025]
    with (ROOT/'results/decade_predictions.csv').open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    result={'status':'NUMERIC_ONLY_EXPLORATORY','ten_year':summary(ten),
        'by_year':{str(year):summary([r for r in rows if r['year']==year]) for year in range(2016,2027)},
        '2016_2020':summary([r for r in ten if r['year']<=2020]),'2021_2025':summary([r for r in ten if r['year']>=2021]),
        'evaluation_start':ten[0]['date'],'last_ten_year_target_end':ten[-1]['target_end'],
        'excluded_windows':excluded,'cross_2025_2026_boundary_excluded_origins':boundary,
        'news_10_year_test_executed':False,'source_provenance_verified':False,'current_forecast_issued':False,
        'minimum_index_lag_hours':min(r['min_index_lag_hours'] for r in rows)}
    (ROOT/'results/decade_results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':main()

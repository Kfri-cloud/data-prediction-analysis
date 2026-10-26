from pathlib import Path
from datetime import datetime,timezone
import csv,json,hashlib
import numpy as np
from run_market import load_bars,at_origin,cutoff_for,NAMES
from run_decade import train_indices
from run_pilot import ridge

ROOT=Path(__file__).resolve().parent
MONTHS=['2025-10','2025-11','2025-12']+[f'2026-{m:02}' for m in range(1,11)]

def metrics(rows):
    if not rows:return {'n':0,'mae_pp':None,'index_improvement_pct':None}
    m={k:float(np.mean([abs(r[k]-r['actual']) for r in rows])) for k in ['D0','D1','DM']}
    return {'n':len(rows),'mae_pp':m,'index_improvement_pct':100*(m['D1']-m['DM'])/m['D1'] if m['D1'] else None,
        'direction_hits':{k:sum(np.sign(r[k])==np.sign(r['actual']) for r in rows).item() for k in ['D1','DM']},
        'first_origin':rows[0]['date'],'last_target_end':max(r['target_end'] for r in rows)}

def main():
    lock=json.loads((ROOT/'results/decade_lock.json').read_text())
    for f,h in lock['sha256'].items():assert hashlib.sha256((ROOT/f).read_bytes()).hexdigest()==h,f
    bars={n:load_bars(ROOT/f'data/decade/{n}.json') for n in NAMES+['usdkrw']};fx=bars['usdkrw']
    start=next(i for i,(t,v) in enumerate(fx) if datetime.fromtimestamp(t,timezone.utc).year>=2012)
    # Use the original snapshot time, not a later wall-clock as if fresh prices were collected.
    asof=max(datetime.fromisoformat(s['retrieved_at_utc']).timestamp() for s in json.loads((ROOT/'results/decade_sources.json').read_text()))
    samples=[];pending=[]
    for i in range(start,len(fx),12):
        date=datetime.fromtimestamp(fx[i][0],timezone.utc).date().isoformat();cutoff=cutoff_for(date)
        if i+11>=len(fx) or fx[i+11][0]+48*3600>asof:
            if date[:7] in MONTHS and cutoff<=asof:pending.append(date)
            continue
        feat,latest=at_origin(fx,cutoff);last=next(v for t,v in fx if t==latest)
        d=datetime.fromisoformat(date);base=feat+[np.sin(d.month*2*np.pi/12),np.cos(d.month*2*np.pi/12)]
        extra=[]
        for n in NAMES:extra+=at_origin(bars[n],cutoff)[0]
        end=fx[i+11][0]
        samples.append({'date':date,'target_end':datetime.fromtimestamp(end,timezone.utc).date().isoformat(),
            'cutoff':cutoff,'label_available':end+48*3600,'base':base,'market':base+extra,
            'actual':float(100*(np.mean([v for t,v in fx[i:i+12]])/last-1))})
    X=np.array([s['base'] for s in samples]);M=np.array([s['market'] for s in samples]);y=np.array([s['actual'] for s in samples])
    previous={r['date']:r for r in csv.DictReader((ROOT/'results/decade_predictions.csv').open())}
    rows=[];matched=0;restored=[]
    for i,s in enumerate(samples):
        if s['date'][:7] not in MONTHS:continue
        train=train_indices(samples,s['cutoff']);assert len(train)>=40
        row={'date':s['date'],'month':s['date'][:7],'target_end':s['target_end'],'training_n':len(train),'actual':s['actual'],
             'D0':0.,'D1':ridge(X[train],y[train],X[i]),'DM':ridge(M[train],y[train],M[i])}
        if s['date'] in previous:
            for k in ['actual','D0','D1','DM']:assert abs(row[k]-float(previous[s['date']][k]))<1e-10
            matched+=1
        else:
            assert s['date']=='2025-12-19';restored.append(s['date'])
        rows.append(row)
    with (ROOT/'results/monthly_predictions.csv').open('w',encoding='utf8',newline='') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    months={m:dict(metrics([r for r in rows if r['month']==m]),pending_origins=[d for d in pending if d[:7]==m],calendar_month_complete=m<'2026-10') for m in MONTHS}
    result={'status':'DESCRIPTIVE_MONTHLY_GROUPING','snapshot_asof_utc':datetime.fromtimestamp(asof,timezone.utc).isoformat(),
        'months':months,'all':metrics(rows),'existing_predictions_matched':matched,'restored_year_boundary_origins':restored,
        'horizon':'12 available daily FX observations, NOT one calendar month','grouped_by':'forecast origin month',
        'news_included':False,'new_holdout':False,'source_provenance_verified':False,
        'input_sha256':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in ['results/decade_predictions.csv','results/decade_lock.json','monthly_protocol.json','run_monthly.py']}}
    (ROOT/'results/monthly_results.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))

if __name__=='__main__':main()

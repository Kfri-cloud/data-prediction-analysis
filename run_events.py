"""Conservative rule-based event candidates, with explicit abstention."""
from pathlib import Path
from datetime import datetime, timezone
import csv, hashlib, json, re
import numpy as np
from run_pilot import base_features, event_text, eligible_train, ridge, block_interval
from run_keywords import keyword_features

ROOT=Path(__file__).resolve().parent
UP=r'\b(?:increase[ds]?|increasing|rose|rise[sn]?|rising|raise[ds]?|raising|hike[ds]?|hiking|surge[ds]?|accelerat\w*|strengthen\w*)\b'
DOWN=r'\b(?:decrease[ds]?|decreasing|fell|fall[sn]?|falling|lower\w*|cut[st]?|cutting|declin\w*|slow\w*|eas\w*|weaken\w*)\b'
ABOVE=r'\b(?:above|exceed\w*|surpass\w*|higher than|stronger than|better than)\b.{0,45}\b(?:expectations|expected|estimates|forecast[s]?)\b'
BELOW=r'\b(?:below|miss\w*|lower than|weaker than|worse than)\b.{0,45}\b(?:expectations|expected|estimates|forecast[s]?)\b'
NEGATION=r"\b(?:not|no|never|without|didn t|doesn t|isn t|wasn t|hasn t|failed to)\b"
MODAL=r'\b(?:may|might|could|would|will|anticipated|projected|expected to|plans? to|planning to|forecast to|likely to)\b'
ACTORS={
    'US':r'\b(?:united states|u s|federal reserve|fomc|bureau of labor statistics|american)\b',
    'KR':r'\b(?:south korea|south korean|bank of korea|korean|korea)\b',
    'other':r'\b(?:china|chinese|european central bank|ecb|eurozone|japan|japanese|bank of japan|bank of england|united kingdom|australia|canada)\b'
}

def clauses(text):
    text=re.sub(r'\bU\.S\.', 'United States', text, flags=re.I)
    text=re.sub(r'<\d+>', ';', text)
    text=re.sub(r'\[\d+\]','',text)
    return [s.strip() for s in re.split(r'(?<!\d)[.!?;](?!\d)',text) if re.search('[a-zA-Z]',s)]

def extract(text,dictionary):
    records=[]
    for sentence in clauses(text):
        normalized=' '.join(re.findall(r'[a-z]+',sentence.lower()))
        topics=[topic for topic,terms in dictionary.items() if any(re.search(r'\b'+re.escape(t)+r'\b',normalized) for t in terms)]
        actors=[actor for actor,pattern in ACTORS.items() if re.search(pattern,normalized)]
        topic=topics[0] if len(topics)==1 else None
        actor=actors[0] if len(actors)==1 else 'unknown'
        reason='single_topic_candidate'
        direction=surprise=0
        negated=bool(re.search(NEGATION,normalized)); modal=bool(re.search(MODAL,normalized))
        if topic is None: reason='no_or_multiple_topics'
        elif negated: reason='negation'
        elif modal: reason='forward_looking_modality'
        else:
            above=bool(re.search(ABOVE,normalized));below=bool(re.search(BELOW,normalized))
            change_text=re.sub(ABOVE,' ',re.sub(BELOW,' ',normalized))
            up=bool(re.search(UP,change_text));down=bool(re.search(DOWN,change_text))
            direction=int(up)-int(down) if up!=down else 0
            surprise=int(above)-int(below) if above!=below else 0
            if (up and down) or (above and below):
                direction=surprise=0;reason='conflicting_cues'
            elif direction==surprise==0: reason='no_direction_or_surprise'
        records.append({'topic':topic,'actor':actor,'direction':direction,'surprise':surprise,'reason':reason,
                        'sentence_sha256':hashlib.sha256(sentence.encode()).hexdigest()})
    return records

def structured_features(text,dictionary):
    records=extract(text,dictionary);topics=list(dictionary);n=max(1,len(records))
    directions=[sum(r['direction'] for r in records if r['topic']==t)/n for t in topics]
    surprises=[sum(r['surprise'] for r in records if r['topic']==t)/n for t in topics]
    actors=[sum(r['actor']==a for r in records)/n for a in ['US','KR','other']]
    policy=[sum(r['direction'] for r in records if r['topic']=='monetary_policy' and r['actor']==a)/n for a in ['US','KR']]
    abstain=sum(r['direction']==0 and r['surprise']==0 for r in records)/n
    return np.array(directions+surprises+actors+policy+[abstain]),records

def summary(rows):
    y=np.array([r['actual'] for r in rows]);keys=['B1','K1','Sdir','Sfull','Sstale']
    err={k:np.abs(y-np.array([r[k] for r in rows])) for k in keys}
    mae={k:float(v.mean()) for k,v in err.items()}
    return {'n':len(rows),'mae_pp':mae,
        'improvement_vs_numeric_pct':{k:100*(mae['B1']-mae[k])/mae['B1'] for k in keys},
        'primary_improvement_vs_keywords_pct':100*(mae['K1']-mae['Sfull'])/mae['K1'],
        'primary_delta_pp':float((err['K1']-err['Sfull']).mean()),
        'primary_descriptive_block_ci_pp':block_interval(err['K1']-err['Sfull']),
        'direction_accuracy':{k:float(np.mean(np.sign(y)==np.sign([r[k] for r in rows]))) for k in keys}}

def main():
    files=['event_protocol.json','run_events.py','keyword_dictionary.json','run_keywords.py','run_pilot.py',
           'data/timesx_krw.json','results/keyword_predictions.csv']
    hashes={f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest() for f in files}
    lock=ROOT/'results/event_lock.json'
    if lock.exists():
        assert json.loads(lock.read_text())['sha256']==hashes,'Frozen event experiment changed'
    else:lock.write_text(json.dumps({'frozen_at_utc':datetime.now(timezone.utc).isoformat(),'prior_results_seen':True,'sha256':hashes},indent=2))
    dictionary=json.loads((ROOT/'keyword_dictionary.json').read_text())
    ss=sorted(json.loads((ROOT/'data/timesx_krw.json').read_text(encoding='utf8'))['samples'],key=lambda s:s['date'])
    base=np.stack([base_features(s) for s in ss])
    kw=np.stack([keyword_features(event_text(s),dictionary) for s in ss])
    count=np.array([s['metadata']['event_count'] for s in ss])[:,None]
    k1=np.column_stack([base,kw,count]);sf=[];audit=[]
    for s in ss:
        feature,recs=structured_features(event_text(s),dictionary);sf.append(feature)
        audit += [dict(date=s['date'],**r) for r in recs]
    sf=np.stack(sf);stale=np.vstack([np.zeros((1,sf.shape[1])),sf[:-1]])
    arms={'Sdir':np.column_stack([k1,sf[:,:8]]),'Sfull':np.column_stack([k1,sf]),'Sstale':np.column_stack([k1,stale])}
    y=np.array([100*(np.mean(s['future_time']['value'])/s['past_time']['value'][-1]-1) for s in ss])
    old=list(csv.DictReader((ROOT/'results/keyword_predictions.csv').open(encoding='utf8')));lookup={s['date']:i for i,s in enumerate(ss)}
    rows=[]
    for o in old:
        i=lookup[o['date']];train=eligible_train(ss,o['date'])
        assert len(train)==int(o['training_n']) and abs(y[i]-float(o['actual']))<1e-10
        assert abs(ridge(k1[train],y[train],k1[i])-float(o['K1']))<1e-10
        row={k:o[k] for k in ['date','block','training_n','latest_train_target']}
        row.update({k:float(o[k]) for k in ['actual','B1','K1']})
        row.update({k:ridge(X[train],y[train],X[i]) for k,X in arms.items()});rows.append(row)
    for filename,records in [('event_predictions.csv',rows),('event_extractions.csv',audit)]:
        with (ROOT/'results'/filename).open('w',encoding='utf8',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(records[0]));w.writeheader();w.writerows(records)
    report={'status':'POST_HOC_EXPLORATORY_NOT_VALIDATED','all':summary(rows),
        'blocks':{b:summary([r for r in rows if r['block']==b]) for b in ['development','confirmation','latest_holdout']},
        'extraction_audit':{'clauses':len(audit),'direction_candidates':sum(r['direction']!=0 for r in audit),
            'surprise_candidates':sum(r['surprise']!=0 for r in audit),'explicit_single_actor':sum(r['actor']!='unknown' for r in audit),
            'abstentions':sum(r['direction']==0 and r['surprise']==0 for r in audit),
            'semantic_accuracy_manually_measured':False},
        'features':22,'new_untouched_holdout':False,'source_provenance_verified':False,
        'limitations':['Heuristic candidates, not verified relations','Qualitative surprise only','Repeated exploration of identical outcomes','No current probability or Seoul SME claim']}
    (ROOT/'results/event_results.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()

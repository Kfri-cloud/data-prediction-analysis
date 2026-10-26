from pathlib import Path
from datetime import datetime,timezone
from concurrent.futures import ThreadPoolExecutor
import urllib.request,json,hashlib
ROOT=Path(__file__).resolve().parent

def fetch(job):
    region,problem=job;code=problem['indicator']
    folder=ROOT/'data/social'/region;folder.mkdir(parents=True,exist_ok=True)
    url=f'https://api.worldbank.org/v2/country/{region}/indicator/{code}?format=json&date=1990:2025&per_page=1000'
    request=urllib.request.Request(url,headers={'User-Agent':'social-prediction-research/0.1'})
    try:
        payload=urllib.request.urlopen(request,timeout=45).read();data=json.loads(payload)
        if not isinstance(data,list) or len(data)!=2 or not isinstance(data[1],list):raise ValueError('unexpected response')
        path=folder/(problem['id']+'.json');path.write_bytes(payload)
        points=[x for x in data[1] if x['value'] is not None]
        return {'region':region,'id':problem['id'],'url':url,'sha256':hashlib.sha256(payload).hexdigest(),
            'rows':len(points),'first_year':min([int(x['date']) for x in points],default=None),
            'last_year':max([int(x['date']) for x in points],default=None),
            'lastupdated':data[0].get('lastupdated'),'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),
            'historical_release_dates_verified':False,'status':'downloaded'}
    except Exception as e:return {'region':region,'id':problem['id'],'url':url,'status':'download_failed','reason':str(e)}

if __name__=='__main__':
    lockpath=ROOT/'results/social_lock.json'
    if lockpath.exists():
        lock=json.loads(lockpath.read_text())['sha256']
        prior=json.loads((ROOT/'results/social_sources.json').read_text())
        for item in prior:
            if item['status']!='downloaded':continue
            rel=f'data/social/{item["region"]}/{item["id"]}.json';path=ROOT/rel
            if not path.exists():
                payload=urllib.request.urlopen(item['url'],timeout=45).read()
                if hashlib.sha256(payload).hexdigest()!=lock[rel]:raise ValueError('Provider response changed; cannot restore frozen data')
                path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(payload)
            assert hashlib.sha256(path.read_bytes()).hexdigest()==lock[rel]
        print('Frozen social snapshots verified; no overwrite performed.')
        raise SystemExit(0)
    catalog=json.loads((ROOT/'social_catalog.json').read_text(encoding='utf8'))
    jobs=[(region,p) for region in catalog['regions'] for p in catalog['problems'] if p['indicator']]
    manifest=list(ThreadPoolExecutor(max_workers=4).map(fetch,jobs))
    (ROOT/'results/social_sources.json').write_text(json.dumps(manifest,indent=2))
    print(json.dumps(manifest,indent=2))

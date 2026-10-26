"""Fetch Yahoo chart snapshots; do not mistake retrieval time for historical availability."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,urllib.request,urllib.parse
ROOT=Path(__file__).resolve().parent
SYMBOLS={'sp500':'^GSPC','nasdaq100':'^NDX','kospi':'^KS11','kosdaq':'^KQ11','usdkrw':'KRW=X'}
if __name__=='__main__':
    folder=ROOT/'data/decade';folder.mkdir(exist_ok=True)
    lockpath=ROOT/'results/decade_lock.json'
    expected=json.loads(lockpath.read_text())['sha256'] if lockpath.exists() else {}
    if expected and all((folder/(n+'.json')).exists() for n in SYMBOLS):
        for n in SYMBOLS:
            assert hashlib.sha256((folder/(n+'.json')).read_bytes()).hexdigest()==expected[f'data/decade/{n}.json']
        print('Frozen market snapshots already present and verified; not overwritten.')
        raise SystemExit(0)
    manifest=[]
    for name,symbol in SYMBOLS.items():
        start=int(datetime(2011,1,1,tzinfo=timezone.utc).timestamp())
        end=int(datetime(2026,10,27,tzinfo=timezone.utc).timestamp())
        url='https://query1.finance.yahoo.com/v8/finance/chart/'+urllib.parse.quote(symbol,safe='')+f'?period1={start}&period2={end}&interval=1d'
        request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0'})
        payload=urllib.request.urlopen(request,timeout=45).read()
        data=json.loads(payload);result=data['chart']['result'][0]
        assert result['meta']['symbol']==symbol
        assert len(result['timestamp'])>500
        payload_hash=hashlib.sha256(payload).hexdigest()
        if expected and payload_hash!=expected[f'data/decade/{name}.json']:
            raise ValueError('Provider response changed: cannot recreate frozen snapshot; existing data not overwritten')
        path=folder/(name+'.json');path.write_bytes(payload)
        manifest.append({'name':name,'symbol':symbol,'url':url,'sha256':hashlib.sha256(payload).hexdigest(),
            'rows':len(result['timestamp']),'exchange_timezone':result['meta'].get('exchangeTimezoneName'),
            'retrieved_at_utc':datetime.now(timezone.utc).isoformat(),'historical_vintage_verified':False})
        print(name,len(result['timestamp']),result['meta'].get('shortName'))
    (ROOT/'results/decade_sources.json').write_text(json.dumps(manifest,indent=2))

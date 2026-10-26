from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,urllib.request
ROOT=Path(__file__).resolve().parent
CATALOG=[('PAYEMS','고용','비농업 고용자 수','천 명'),('UNRATE','노동시장','실업률','%'),('RSAFS','소비','소매·음식서비스 판매액','백만 달러'),('INDPRO','생산','산업생산지수','2017=100'),('HOUST','주택공급','민간 주택착공','천 호·계절조정 연율')]
def main():
    folder=ROOT/'data/monthly_domains';folder.mkdir(exist_ok=True);manifest=[]
    for key,field,name,unit in CATALOG:
        url=f'https://fred.stlouisfed.org/graph/?g=1&id={key}&cosd=2000-01-01&coed=2025-12-31'
        download=f'https://fred.stlouisfed.org/graph/fredgraph.csv?id={key}&cosd=2000-01-01&coed=2025-12-31'
        path=folder/f'{key}.csv'
        if not path.exists():
            req=urllib.request.Request(download,headers={'User-Agent':'Mozilla/5.0'})
            path.write_bytes(urllib.request.urlopen(req,timeout=45).read())
        manifest.append(dict(id=key,field=field,name=name,unit=unit,source=f'https://fred.stlouisfed.org/series/{key}',download=download,sha256=hashlib.sha256(path.read_bytes()).hexdigest()))
        print(key,path.stat().st_size,flush=True)
    dest=ROOT/'results/monthly_domains_sources.json'
    if dest.exists():assert json.loads(dest.read_text(encoding='utf8'))['sources']==manifest
    else:dest.write_text(json.dumps(dict(retrieved_at=datetime.now(timezone.utc).isoformat(),sources=manifest),ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()

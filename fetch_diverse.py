from pathlib import Path
import urllib.request,json,hashlib
ROOT=Path(__file__).resolve().parent
COMMIT='26bc70cfa669407c71ae1ad6ce2194be9cfe9a0b'
CATALOG=[
 ('brent','에너지','브렌트유','price','CommodityPrice/EnergyAndFuels/brent_usd_bbl_96_12_12_10events.json'),
 ('coal','에너지','석탄','price','CommodityPrice/EnergyAndFuels/coal_usd_t_96_12_12_10events.json'),
 ('ethanol','에너지','에탄올','price','CommodityPrice/EnergyAndFuels/ethanol_usd_gal_96_12_12_10events.json'),
 ('wheat','농산물','밀','price','CommodityPrice/CropsAndStaples/wheat_usd_bu_96_12_12_10events.json'),
 ('corn','농산물','옥수수','price','CommodityPrice/LivestockAndFoodProducts/corn_usd_bu_96_12_12_10events.json'),
 ('soybeans','농산물','대두','price','CommodityPrice/LivestockAndFoodProducts/soybeans_usd_bu_96_12_12_10events.json'),
 ('ai','기술','AI','search','SearchTrend/electronic_technology/artificial_intelligence_96_12_4_10events.json'),
 ('robotics','기술','로봇','search','SearchTrend/electronic_technology/robotics_96_12_4_10events.json'),
 ('cybersecurity','기술','사이버보안','search','SearchTrend/society/cybersecurity_96_12_4_10events.json'),
 ('air_travel','여가·여행','항공여행','search','SearchTrend/traffic/air_travel_96_12_4_10events.json'),
 ('music','여가·여행','음악축제','search','SearchTrend/arts/music_festivals_96_12_4_10events.json'),
 ('esports','여가·여행','e스포츠','search','SearchTrend/arts/esports_96_12_4_10events.json'),
 ('black_friday','소비','블랙프라이데이','search','SearchTrend/shopping/black_friday_deals_96_12_4_10events.json'),
 ('school','소비','개학 준비','search','SearchTrend/shopping/back_to_school_96_12_4_10events.json'),
 ('air_conditioner','소비','에어컨','search','SearchTrend/shopping/air_conditioner_96_12_4_10events.json')]
def main():
    folder=ROOT/'data/diverse';folder.mkdir(exist_ok=True);manifest=[]
    for key,field,name,kind,path in CATALOG:
        dest=folder/f'{key}.json';url=f'https://raw.githubusercontent.com/haoxin1998/TimesX-project/{COMMIT}/Datasets/{path}'
        if not dest.exists():dest.write_bytes(urllib.request.urlopen(url,timeout=60).read())
        manifest.append(dict(id=key,field=field,name=name,kind=kind,url=url,sha256=hashlib.sha256(dest.read_bytes()).hexdigest()))
        print(key,len(json.loads(dest.read_bytes())['samples']),flush=True)
    out=ROOT/'results/diverse_sources.json'
    if out.exists():assert json.loads(out.read_text(encoding='utf8'))==manifest
    else:out.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()

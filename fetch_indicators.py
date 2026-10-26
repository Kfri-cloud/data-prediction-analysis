"""Pinned public research snapshots. Raw data are not republished."""
from pathlib import Path
import json, hashlib, urllib.request
ROOT=Path(__file__).resolve().parent
COMMIT='26bc70cfa669407c71ae1ad6ce2194be9cfe9a0b'
CATALOG=[
 ('brent','브렌트유','EnergyAndFuels/brent_usd_bbl'),
 ('gasoline','휘발유','EnergyAndFuels/gasoline_usd_gal'),
 ('coal','석탄','EnergyAndFuels/coal_usd_t'),
 ('gold','금','StrategicAndHighValueMaterials/gold_usd_t_oz'),
 ('silver','은','StrategicAndHighValueMaterials/silver_usd_t_oz'),
 ('copper','구리','RawMaterialsAndConstruction/copper_usd_lbs'),
 ('aluminum','알루미늄','RawMaterialsAndConstruction/aluminum_usd_t'),
 ('corn','옥수수','LivestockAndFoodProducts/corn_usd_bu'),
 ('soybeans','대두','LivestockAndFoodProducts/soybeans_usd_bu'),
 ('coffee','커피','LivestockAndFoodProducts/coffee_usd_lbs')]
def main():
    folder=ROOT/'data/indicators';folder.mkdir(exist_ok=True)
    manifest=[]
    for key,name,path in CATALOG:
        url=f'https://raw.githubusercontent.com/haoxin1998/TimesX-project/{COMMIT}/Datasets/CommodityPrice/{path}_96_12_12_10events.json'
        target=folder/f'{key}.json'
        if not target.exists():target.write_bytes(urllib.request.urlopen(url,timeout=60).read())
        manifest.append(dict(id=key,name=name,url=url,sha256=hashlib.sha256(target.read_bytes()).hexdigest()))
        print(key,len(json.loads(target.read_bytes())['samples']),flush=True)
    dest=ROOT/'results/indicator_sources.json'
    if dest.exists():assert json.loads(dest.read_text())==manifest,'Source changed'
    else:dest.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf8')
if __name__=='__main__':main()

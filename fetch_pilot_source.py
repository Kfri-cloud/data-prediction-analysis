"""Download pinned author data without running remote code."""
from pathlib import Path
import hashlib, json, urllib.request

ROOT=Path(__file__).resolve().parent
COMMIT='26bc70cfa669407c71ae1ad6ce2194be9cfe9a0b'
URL=f'https://raw.githubusercontent.com/haoxin1998/TimesX-project/{COMMIT}/Datasets/Currency/usdtokrw_exchangerate_96_12_12_10events.json'
if __name__=='__main__':
    lock=json.loads((ROOT/'results/pilot_lock.json').read_text())
    data=urllib.request.urlopen(URL,timeout=45).read()
    if hashlib.sha256(data).hexdigest()!=lock['data_sha256']:
        raise ValueError('Downloaded source does not match frozen experiment')
    (ROOT/'data').mkdir(exist_ok=True)
    (ROOT/'data/timesx_krw.json').write_bytes(data)
    (ROOT/'data/timesx_commit.txt').write_text(COMMIT)
    print('Pinned data downloaded and SHA256 verified')

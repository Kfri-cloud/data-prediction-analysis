import unittest,json,csv
from pathlib import Path
import numpy as np
from run_indicators import validate,summarize
ROOT=Path(__file__).resolve().parent
class IndicatorTests(unittest.TestCase):
    def test_future_overlap_rejected(self):
        ss=json.loads((ROOT/'data/indicators/brent.json').read_text(encoding='utf8'))['samples'][:1]
        ss[0]['past_time']['timestamp'][-1]=ss[0]['future_time']['timestamp'][0]
        with self.assertRaises(AssertionError):validate(ss)
    def test_all_predictions_and_temporal_boundary(self):
        rows=list(csv.DictReader((ROOT/'results/indicator_predictions.csv').read_text(encoding='utf8').splitlines()))
        self.assertEqual(len({r['indicator'] for r in rows}),10)
        for r in rows:
            self.assertLess(r['latest_train_target'][:10],r['date'])
            self.assertAlmostEqual(float(r['Cavg']),.5*(float(r['M'])+float(r['Sdir'])),places=12)
    def test_metrics_independently_recomputed(self):
        rows=list(csv.DictReader((ROOT/'results/indicator_predictions.csv').read_text(encoding='utf8').splitlines()))
        report=json.loads((ROOT/'results/indicator_results.json').read_text(encoding='utf8'))
        for result in report['results']:
            selected=[r for r in rows if r['indicator']==result['id']]
            for k in ['B0','B1','M','Sdir','Cavg']:
                mae=sum(abs(float(r['actual'])-float(r[k])) for r in selected)/len(selected)
                self.assertAlmostEqual(mae,result['summary']['mae_pp'][k],places=12)
            self.assertFalse(result['provenance_verified'])
if __name__=='__main__':unittest.main()

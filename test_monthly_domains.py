import unittest,csv,json
import numpy as np
from run_monthly_domains import ROOT,predict,choose
class MonthlyTests(unittest.TestCase):
    def test_future_mutation_invariance(self):
        y=np.arange(160,dtype=float)+50
        before=predict(y,100,'PAYEMS');y[101:]=1e8
        self.assertEqual(before,predict(y,100,'PAYEMS'))
    def test_selection_ignores_future(self):
        row=dict(target_month='2020-02-01',actual=99,Last=1,Seasonal=2,Drift=3,Ridge=4,Analog=5)
        self.assertEqual(choose([row],'2020-01-01'),('Last',[]))
    def test_saved_boundaries_and_metrics(self):
        rows=list(csv.DictReader((ROOT/'results/monthly_domains_predictions.csv').read_text().splitlines()))
        self.assertEqual(len(rows),597)
        for r in rows:
            self.assertLess(r['latest_train_target'],r['target_month'])
            self.assertLess(r['latest_selection_target'],r['target_month'])
            self.assertEqual(float(r['Selected']),float(r[r['chosen']]))
        for r in json.loads((ROOT/'results/monthly_domains_results.json').read_text(encoding='utf8'))['results']:
            selected=[x for x in rows if x['id']==r['id']]
            self.assertEqual(len(selected),117 if r['id']=='UNRATE' else 120)
            for k,v in r['summary']['mae'].items():self.assertAlmostEqual(v,sum(abs(float(x['actual'])-float(x[k])) for x in selected)/len(selected),places=10)
    def test_missing_input_abstains(self):
        y=np.arange(160,dtype=float)+50;y[95]=np.nan
        self.assertIsNone(predict(y,100,'PAYEMS'))
if __name__=='__main__':unittest.main()

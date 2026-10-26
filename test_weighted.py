import unittest,csv,json
import numpy as np
from run_weighted import split_news,choose_weight,ROOT
class WeightedTests(unittest.TestCase):
    def test_outcome_not_expectation(self):
        result,other=split_news('Production rose by 5 percent. Production may rise next year. The bank has not raised rates.')
        self.assertEqual(len(result),1);self.assertEqual(len(other),2)
    def test_weight_constraints_and_fallback(self):
        a=np.ones(8);b=np.zeros(8);y=np.zeros(8)
        self.assertEqual(choose_weight(a,b,y,False),0)
        self.assertEqual(choose_weight(a,b,y,True),.5)
        self.assertEqual(choose_weight(a[:2],b[:2],y[:2],False),.5)
    def test_all_temporal_boundaries_and_mixture(self):
        rows=list(csv.DictReader((ROOT/'results/weighted_predictions.csv').read_text().splitlines()))
        self.assertEqual(len(rows),473)
        for r in rows:
            self.assertLess(r['weight_latest_target'][:10],r['date'])
            self.assertLess(r['latest_train_target'][:10],r['date'])
            self.assertAlmostEqual(float(r['Weighted']),.5*(float(r['Windex'])+float(r['Wnews'])),places=12)
            self.assertIn(float(r['nasdaq']),[.5,.75,1]);self.assertIn(float(r['outcome']),[.5,.75,1])
    def test_report_mae(self):
        rows=list(csv.DictReader((ROOT/'results/weighted_predictions.csv').read_text().splitlines()))
        for r in json.loads((ROOT/'results/weighted_results.json').read_text(encoding='utf8'))['results']:
            selected=[x for x in rows if x['indicator']==r['id']]
            for model,mae in r['summary']['mae'].items():
                self.assertAlmostEqual(mae,sum(abs(float(x['actual'])-float(x[model])) for x in selected)/len(selected),places=12)
if __name__=='__main__':unittest.main()

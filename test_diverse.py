import unittest,csv,json
import numpy as np
from run_diverse import classify,category_weights,blend,target,ROOT
class DiverseTests(unittest.TestCase):
    def test_categories_and_abstention(self):
        p=classify('Investor confidence improved. Output rose by 5 percent. Earnings were above expectations. Output may rise. The bank has not raised rates.')
        self.assertEqual([len(p[g]) for g in ['psyche','outcome','surprise','unknown']],[1,1,1,2])
        self.assertEqual(len(classify('Output rose but fears increased.')['unknown']),1)
    def test_weight_priority_missing_and_fallback(self):
        w=category_weights([1,1,1,1],3)
        self.assertGreater(w[0],w[1]);self.assertAlmostEqual(sum(w),1)
        self.assertEqual(category_weights([0,1,0,0],3)[0],0)
        self.assertEqual(blend(np.ones(4),[0,0,0,0],3,7),7)
    def test_search_zero_and_scale_not_clipped(self):
        s={'past_time':{'value':[0]},'future_time':{'value':[300]*12}}
        self.assertEqual(target(s,'search'),300)
    def test_output_temporal_boundaries_and_blend(self):
        rows=list(csv.DictReader((ROOT/'results/diverse_predictions.csv').read_text().splitlines()))
        self.assertEqual(len({r['indicator'] for r in rows}),15)
        for r in rows:
            self.assertLess(r['latest_train_target'][:10],r['date'])
            self.assertLess(r['weight_latest_target'][:10],r['date'])
            self.assertAlmostEqual(float(r['Psyche']),.5*(float(r['index_prediction'])+float(r['news_prediction'])),places=12)
    def test_metrics_and_nonoverlap(self):
        rows=list(csv.DictReader((ROOT/'results/diverse_predictions.csv').read_text().splitlines()))
        report=json.loads((ROOT/'results/diverse_results.json').read_text(encoding='utf8'))
        for result in report['results']:
            selected=[r for r in rows if r['indicator']==result['id']]
            for k,v in result['summary']['mae'].items():
                self.assertAlmostEqual(v,sum(abs(float(r['actual'])-float(r[k])) for r in selected)/len(selected),places=12)
            independent=[];end=''
            for r in selected:
                if r['date']>end:independent.append(r);end=r['target_end']
            self.assertEqual(len(independent),result['nonoverlap']['n'])
if __name__=='__main__':unittest.main()

import unittest,json,csv
from run_social_transfer import candidates,select,ROOT,MODELS
class SocialTransferTests(unittest.TestCase):
    def test_future_data_does_not_change_candidates(self):
        d={y:float(y-1980) for y in range(1990,2026)}
        a=candidates(d,2010,'aging');d[2011]=99999;d[2025]=99999
        self.assertEqual(a,candidates(d,2010,'aging'))
    def test_selection_ignores_future_targets(self):
        h=[dict(target_year=y,actual=1.,N0=1.,Trend=2.,N1=3.,Analog=4.) for y in range(2000,2011)]
        a=select(h,2005);h[-1]['actual']=1e9
        self.assertEqual(a,select(h,2005));self.assertEqual(a[0],'N0')
    def test_boundaries_and_values(self):
        rows=list(csv.DictReader((ROOT/'results/social_transfer_predictions.csv').read_text().splitlines()))
        for r in rows:
            self.assertLessEqual(int(r['latest_training_target']),int(r['origin_year']))
            self.assertLessEqual(int(r['latest_selection_target']),int(r['origin_year']))
            self.assertAlmostEqual(float(r['Selected']),float(r[r['chosen']]))
        ns=list(csv.DictReader((ROOT/'results/social_transfer_neighbors.csv').read_text().splitlines()))
        for n in ns:self.assertLessEqual(int(n['target_year']),int(n['forecast_origin']))
    def test_metrics_and_projection_gate(self):
        rows=list(csv.DictReader((ROOT/'results/social_transfer_predictions.csv').read_text().splitlines()))
        result=json.loads((ROOT/'results/social_transfer_results.json').read_text(encoding='utf8'))['results']
        self.assertEqual(len(result),20)
        self.assertEqual(sum(r['projection_2026'] is not None for r in result),6)
        for r in result:
            if 'summary' not in r:self.assertIsNone(r['projection_2026']);continue
            selected=[x for x in rows if x['region']==r['region'] and x['problem']==r['problem']]
            for m,v in r['summary']['mae'].items():self.assertAlmostEqual(v,sum(abs(float(x['actual'])-float(x[m])) for x in selected)/len(selected),places=12)
            if r['projection_2026']:self.assertEqual(r['latest_year'],2025)
if __name__=='__main__':unittest.main()

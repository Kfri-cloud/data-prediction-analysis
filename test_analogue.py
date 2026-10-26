import unittest,json,csv,copy
import numpy as np
from run_analogue import ROOT,distances,neighbors
class AnalogueTests(unittest.TestCase):
    def test_future_rows_do_not_affect_distance(self):
        x=np.array([[0.,1.],[1.,2.],[2.,3.],[4.,5.]])
        a=distances([x],[0,1],2);x[3]=1e9
        np.testing.assert_array_equal(a,distances([x],[0,1],2))
    def test_selection_ignores_outcome_and_removes_overlap(self):
        ss=[dict(date=f'2020-01-{d:02}',future_time=dict(timestamp=[f'2020-01-{d+2:02}'],value=[1])) for d in [1,2,5,8]]
        original=neighbors(ss,[0,1,2,3],[0,1,2,3],3)
        for s in ss:s['future_time']['value']=[999999]
        self.assertEqual(original,neighbors(ss,[0,1,2,3],[0,1,2,3],3))
        self.assertEqual([i for i,_ in original],[0,2,3])
    def test_saved_neighbors_completed_nonoverlap(self):
        rows=list(csv.DictReader((ROOT/'results/analogue_neighbors.csv').read_text().splitlines()));groups={}
        for r in rows:
            self.assertLess(r['neighbor_end'],r['origin'])
            groups.setdefault((r['indicator'],r['origin'],r['model']),[]).append(r)
        for group in groups.values():
            ordered=sorted(group,key=lambda r:r['neighbor_origin'])
            for a,b in zip(ordered,ordered[1:]):self.assertLess(a['neighbor_end'],b['neighbor_origin'])
    def test_prediction_from_saved_cases(self):
        neighbors=list(csv.DictReader((ROOT/'results/analogue_neighbors.csv').read_text().splitlines()))
        rows=list(csv.DictReader((ROOT/'results/analogue_predictions.csv').read_text().splitlines()))
        self.assertEqual(len(rows),383)
        lookup={}
        for n in neighbors:lookup.setdefault((n['indicator'],n['origin'],n['model']),[]).append(float(n['residual']))
        for r in rows:
            for model in ['Analog5','News5','Analog3']:
                values=lookup[(r['indicator'],r['date'],model)]
                expected=float(r['Naive'])+(float(np.median(values)) if len(values)>=3 else 0)
                self.assertAlmostEqual(float(r[model]),expected,places=12)
    def test_mae_recomputed(self):
        rows=list(csv.DictReader((ROOT/'results/analogue_predictions.csv').read_text().splitlines()))
        for r in json.loads((ROOT/'results/analogue_results.json').read_text(encoding='utf8'))['results']:
            selected=[x for x in rows if x['indicator']==r['id']]
            for model,value in r['summary']['mae'].items():self.assertAlmostEqual(value,sum(abs(float(x['actual'])-float(x[model])) for x in selected)/len(selected),places=12)
if __name__=='__main__':unittest.main()

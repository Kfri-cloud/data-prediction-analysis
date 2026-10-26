import unittest
from run_social import observations,feature,fit_prediction,bound
class SocialTests(unittest.TestCase):
    def test_country_mismatch_rejected(self):
        row={'countryiso3code':'USA','indicator':{'id':'X'},'date':'2020','value':1}
        with self.assertRaises(ValueError):observations([{},[row]],'KOR','X')
    def test_missing_year_not_interpolated(self):
        self.assertIsNone(feature({2010:1,2012:2,2013:3},2013))
    def test_future_changes_cannot_affect_fit(self):
        d={y:float(y-1990) for y in range(1990,2026)};a=fit_prediction(d,2020,'aging')
        d.update({y:99999. for y in range(2021,2026)})
        self.assertEqual(a,fit_prediction(d,2020,'aging'));self.assertLessEqual(a['latest_training_target_year'],2020)
    def test_short_series_rejected(self):
        self.assertIsNone(fit_prediction({y:1. for y in range(2020,2026)},2025,'aging'))
    def test_domain_bounds(self):
        self.assertEqual(bound(-1,'fertility'),0);self.assertEqual(bound(-1,'living_cost'),-1)
        self.assertEqual(bound(120,'youth_jobs'),100);self.assertEqual(bound(120,'aging'),120)
if __name__=='__main__':unittest.main()

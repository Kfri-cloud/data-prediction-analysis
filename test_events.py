import json,unittest
from pathlib import Path
from run_events import extract,structured_features

D=json.loads((Path(__file__).parent/'keyword_dictionary.json').read_text())

class EventTests(unittest.TestCase):
    def one(self,text):return extract(text,D)[0]
    def test_us_hike(self):
        r=self.one('The U.S. Federal Reserve raised interest rates.')
        self.assertEqual((r['topic'],r['actor'],r['direction']),('monetary_policy','US',1))
    def test_korean_cut(self):
        r=self.one('The Bank of Korea cut interest rates.')
        self.assertEqual((r['actor'],r['direction']),('KR',-1))
    def test_negation_abstains(self):
        self.assertEqual(self.one('The Federal Reserve did not raise interest rates.')['direction'],0)
    def test_forecast_abstains(self):
        self.assertEqual(self.one('The Federal Reserve is expected to cut interest rates.')['direction'],0)
    def test_conflicting_topics_abstain(self):
        self.assertEqual(self.one('Inflation fell while employment increased.')['direction'],0)
    def test_conflicting_directions_abstain(self):
        self.assertEqual(self.one('Inflation rose then fell.')['direction'],0)
    def test_surprise_distinct_from_change(self):
        r=self.one('Inflation declined but remained above expectations.')
        self.assertEqual((r['direction'],r['surprise']),(-1,1))
    def test_missing_actor_not_assumed(self):
        self.assertEqual(self.one('Inflation increased.')['actor'],'unknown')
    def test_lower_than_expected_is_not_a_time_decline(self):
        r=self.one('Inflation was lower than expected.')
        self.assertEqual((r['direction'],r['surprise']),(0,-1))
    def test_multiple_jurisdictions_abstain_actor(self):
        self.assertEqual(self.one('The Federal Reserve and Bank of Korea raised interest rates.')['actor'],'unknown')
    def test_empty_features_finite(self):
        x,records=structured_features('',D)
        self.assertEqual(len(x),22);self.assertEqual(sum(x),0);self.assertEqual(records,[])

if __name__=='__main__':unittest.main()

import unittest
from datetime import datetime,timezone
from run_market import at_origin,cutoff_for

class MarketTests(unittest.TestCase):
    def test_future_and_recent_bars_excluded(self):
        bars=[(i*86400,100+i) for i in range(30)]
        features,last=at_origin(bars,25*86400)
        self.assertEqual(last,23*86400)
        self.assertAlmostEqual(features[0],100*(123/122-1))
    def test_future_mutation_does_not_change_features(self):
        bars=[(i*86400,100+i) for i in range(30)]
        changed=[(t,v if t<=23*86400 else 99999) for t,v in bars]
        self.assertEqual(at_origin(bars,25*86400),at_origin(changed,25*86400))
    def test_stale_history_rejected(self):
        with self.assertRaises(ValueError):at_origin([(i*86400,100+i) for i in range(30)],50*86400)
    def test_insufficient_history_rejected(self):
        with self.assertRaises(ValueError):at_origin([(0,100)],50*86400)
    def test_korea_midnight_utc(self):
        self.assertEqual(datetime.fromtimestamp(cutoff_for('2025-01-02'),timezone.utc).isoformat(),'2025-01-01T15:00:00+00:00')

if __name__=='__main__':unittest.main()

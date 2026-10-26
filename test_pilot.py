import unittest
import numpy as np
from run_pilot import eligible_train, ridge, text_features, block_interval, event_text

class ReplayTests(unittest.TestCase):
    def test_overlapping_and_same_day_labels_are_excluded(self):
        samples=[{'date':'2023-01-01','future_time':{'timestamp':['2023-01-12T00:00:00']}},
                 {'date':'2023-01-10','future_time':{'timestamp':['2023-01-21T00:00:00']}},
                 {'date':'2023-01-05','future_time':{'timestamp':['2023-01-20T00:00:00']}}]
        self.assertEqual(eligible_train(samples,'2023-01-20'),[0])

    def test_unknown_future_target_never_admitted(self):
        s=[{'date':'2099-01-01','future_time':{'timestamp':['2099-01-12T00:00:00']}}]
        self.assertEqual(eligible_train(s,'2024-01-01'),[])

    def test_train_only_scaling_matches_closed_form(self):
        X=np.array([[0.],[2.]])
        # Z = [-1,1], centered y=[-1,1], beta=2/(2+2)=.5
        self.assertAlmostEqual(ridge(X,np.array([0.,2.]),np.array([5.])),3.)

    def test_constant_columns_are_finite(self):
        self.assertAlmostEqual(ridge(np.ones((3,2)),np.array([1.,2.,3.]),np.ones(2)),2.)

    def test_hash_features_are_deterministic_without_fitting(self):
        np.testing.assert_equal(text_features('interest rates rose'),text_features('interest rates rose'))
        self.assertAlmostEqual(np.linalg.norm(text_features('interest rates rose')),1.)

    def test_bootstrap_sign_and_reproducibility(self):
        self.assertEqual(block_interval(np.ones(15)),[1.,1.])
        self.assertEqual(block_interval(np.arange(15)),block_interval(np.arange(15)))

    def test_target_period_prefix_removed(self):
        self.assertEqual(event_text({'scenario':'Prediction target period: 2099. Recent related events (tags): <1> Rates rose.'}),'<1> Rates rose.')

if __name__=='__main__': unittest.main()

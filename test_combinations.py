import unittest
from run_combinations import average,paired_sources
class CombinationTests(unittest.TestCase):
    def row(self,date='2024-01-01',actual='1'):
        return dict(date=date,actual=actual,B1='0',training_n='20',block='development',latest_train_target='2023-12-20')
    def test_weight_is_fixed_and_bounded(self):
        self.assertEqual(average(-2,4),1);self.assertEqual(average(3,3),3)
    def test_different_targets_rejected(self):
        with self.assertRaises(ValueError):paired_sources([self.row()],[self.row(actual='2')])
    def test_different_dates_rejected(self):
        with self.assertRaises(ValueError):paired_sources([self.row()],[self.row(date='2024-02-01')])
    def test_duplicate_origins_rejected(self):
        with self.assertRaises(ValueError):paired_sources([self.row(),self.row()],[self.row()])
    def test_matching_rows_admitted(self):
        self.assertEqual(len(paired_sources([self.row()],[self.row()])),1)
if __name__=='__main__':unittest.main()

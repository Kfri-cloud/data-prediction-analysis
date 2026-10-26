import unittest
from run_decade import train_indices
class DecadeTests(unittest.TestCase):
    def test_unreleased_training_label_excluded(self):
        s=[{'cutoff':1,'label_available':100},{'cutoff':2,'label_available':49},{'cutoff':60,'label_available':40}]
        self.assertEqual(train_indices(s,50),[1])
    def test_equal_available_cutoff_admitted(self):
        self.assertEqual(train_indices([{'cutoff':1,'label_available':50}],50),[0])
if __name__=='__main__':unittest.main()

import unittest
import numpy as np
from run_keywords import keyword_features

class KeywordTests(unittest.TestCase):
    def test_boundaries_prevent_gas_in_vegas(self):
        np.testing.assert_equal(keyword_features('Vegas gasoline gas',{'energy':['gas']}),[1000/3])
    def test_multiword_longest_match_not_double_counted(self):
        np.testing.assert_equal(keyword_features('Interest rates interest rate',{'policy':['interest rate','interest rates']}),[500.])
    def test_punctuation_case_and_empty(self):
        np.testing.assert_equal(keyword_features('CPI, inflation!',{'inflation':['cpi','inflation']}),[1000.])
        np.testing.assert_equal(keyword_features('',{'inflation':['inflation']}),[0.])
    def test_frequency_not_sentiment(self):
        # A deliberate limitation: inflation rising and falling have identical topic counts.
        np.testing.assert_equal(keyword_features('inflation is rising',{'i':['inflation']}),keyword_features('inflation is falling',{'i':['inflation']}))

if __name__=='__main__':unittest.main()

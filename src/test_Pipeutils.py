from nose.tools import *
import numpy as np

from Pipeutils import Pipeutils


def test_dateToMjd():

    putils = Pipeutils()

    sdfits_date_string = '2009-02-10T21:09:00.10'
    result = putils.dateToMjd(sdfits_date_string)
    expected_result = 54872.8812512
    assert_almost_equal(result, expected_result)


def test_masked_array():

    putils = Pipeutils()

    nan = float('nan')
    unmasked = np.array([1, 2, 3, 4, nan, 5, 6., 7.7, nan, 9])
    masked = putils.masked_array(unmasked)
    eq_(len(unmasked), len(masked))
    eq_(np.isnan(unmasked).tolist().count(True), 2)
    eq_(np.isnan(masked).tolist().count(True), 0)
    np.testing.assert_equal(masked.data, unmasked)
    eq_(masked.sum(), 37.7)

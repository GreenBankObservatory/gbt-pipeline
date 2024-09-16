import unittest
import numpy as np
import fitsio

from gbtpipeline.Integration import Integration


@unittest.skip("test data does not exist in the repo; not clear how this ever worked")
class TestIntegration(unittest.TestCase):
    def setUp(self):
        ff = fitsio.FITS("test/TKFPA_29_10rows_test.raw.acs.fits")
        columns = tuple(ff[1].get_colnames())
        self.row = Integration(ff[1][columns][0])

    def test_get(self):
        assert self.row["OBJECT"] == "W51-OFF"
        assert self.row["CAL"] == "T"
        assert self.row["SIG"] == "T"
        assert np.all(self.row["DATA"]) is True
        assert np.any(np.isnan(self.row["DATA"])) is False

    def test_set(self):
        self.row["SIG"] = "A"
        assert self.row["SIG"] == "A"

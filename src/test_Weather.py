from nose.tools import *

from Weather import Weather


class test_Weather:

    def setup(self):
        self.weather = Weather()
        pass

    def test_retrieve_zenith_opacity(self):
        zenith_tau = self.weather.retrieve_zenith_opacity(54210, 23.6e9)
        assert_almost_equal(zenith_tau, 0.1550, places=4)
        zenith_tau = self.weather.retrieve_zenith_opacity(54215.32, 23.6e9)
        assert_almost_equal(zenith_tau, 0.1246, places=4)

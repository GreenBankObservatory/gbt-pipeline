import unittest
import pytest

from gbtpipeline.Weather import Weather


class TestWeather(unittest.TestCase):
    def setUp(self):
        self.weather = Weather()

    def test_retrieve_zenith_opacity(self):
        zenith_tau = self.weather.retrieve_zenith_opacity(54210, 23.6e9)
        pytest.approx(zenith_tau, 0.1550, 4)
        zenith_tau = self.weather.retrieve_zenith_opacity(54215.32, 23.6e9)
        pytest.approx(zenith_tau, 0.1246, 4)

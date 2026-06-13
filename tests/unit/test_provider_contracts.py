from datetime import date

import pytest

from app.core.exceptions import ConfigurationError
from app.domain.models import Point
from app.providers.weather.base import WeatherProvider
from app.providers.weather.open_meteo import OpenMeteoProvider
from app.providers.weather.open_weather import OpenWeatherProvider


def test_open_meteo_is_weather_provider() -> None:
    provider = OpenMeteoProvider()
    assert isinstance(provider, WeatherProvider)


def test_open_weather_requires_key() -> None:
    with pytest.raises(ConfigurationError):
        OpenWeatherProvider(api_key=None)


def test_open_weather_accepts_key() -> None:
    provider = OpenWeatherProvider(api_key="dummy")
    assert provider.api_key == "dummy"

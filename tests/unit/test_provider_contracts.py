from datetime import UTC, date, datetime
from unittest.mock import MagicMock, patch

import pytest
import requests

from app.core.exceptions import ConfigurationError, ProviderError
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


def test_open_meteo_get_hourly_forecast_mocked() -> None:
    provider = OpenMeteoProvider()
    target = date(2024, 6, 1)
    response = {
        "hourly": {
            "time": [
                "2024-06-01T00:00",
                "2024-06-01T01:00",
                "2024-06-01T02:00",
            ],
            "temperature_2m": [15.0, 16.0, 17.0],
            "windspeed_10m": [5.0, 6.0, 7.0],
            "precipitation": [0.0, 0.1, 0.0],
            "precipitation_probability": [10, 20, 30],
            "cloudcover": [20, 25, 30],
        }
    }
    mock_response = MagicMock()
    mock_response.json.return_value = response
    with patch(
        "app.providers.weather.open_meteo.requests.get", return_value=mock_response
    ):
        forecast = provider.get_hourly_forecast(Point(lat=48.0, lon=11.0), target)

    assert len(forecast) == 3
    assert forecast[0].temp_c == 15.0
    assert forecast[0].wind_kmh == 5.0
    assert forecast[0].precip_mm == 0.0
    assert forecast[0].precip_probability == 10.0
    assert forecast[0].cloud_cover == 20.0
    assert forecast[0].time == datetime(2024, 6, 1, 0, 0, tzinfo=UTC)


def test_open_weather_get_hourly_forecast_mocked() -> None:
    provider = OpenWeatherProvider(api_key="dummy")
    target = date(2024, 6, 1)
    response = {
        "hourly": [
            {
                "dt": 1717200000,
                "temp": 15.0,
                "wind_speed": 2.0,
                "pop": 0.1,
                "clouds": 20,
            },
            {
                "dt": 1717286400,
                "temp": 16.0,
                "wind_speed": 3.0,
            },
        ]
    }
    mock_response = MagicMock()
    mock_response.json.return_value = response
    with patch(
        "app.providers.weather.open_weather.requests.get", return_value=mock_response
    ):
        forecast = provider.get_hourly_forecast(Point(lat=48.0, lon=11.0), target)

    assert len(forecast) == 1
    assert forecast[0].temp_c == 15.0
    assert forecast[0].time.date() == target


def test_provider_raises_provider_error_on_http_error() -> None:
    provider = OpenMeteoProvider()
    with patch(
        "app.providers.weather.open_meteo.requests.get",
        side_effect=requests.HTTPError("boom"),
    ):
        with pytest.raises(ProviderError):
            provider.get_hourly_forecast(Point(lat=48.0, lon=11.0), date(2024, 6, 1))

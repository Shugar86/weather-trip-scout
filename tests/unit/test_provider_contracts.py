from datetime import UTC, date, datetime
from json import JSONDecodeError
from unittest.mock import MagicMock, patch

import pytest
import requests

from app.core.exceptions import ConfigurationError, ProviderError
from app.domain.models import Point
from app.providers.geo.base import GeoProvider
from app.providers.geo.overpass import OverpassProvider
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


def test_overpass_is_geo_provider() -> None:
    provider = OverpassProvider()
    assert isinstance(provider, GeoProvider)


def test_overpass_get_candidate_places_mocked() -> None:
    provider = OverpassProvider()
    response = {
        "elements": [
            {
                "id": 123,
                "lat": 48.0,
                "lon": 11.0,
                "tags": {"name": "Test Town", "place": "town"},
            },
            {
                "id": 124,
                "lat": 48.1,
                "lon": 11.1,
                "tags": {"name:en": "No Name Peak", "natural": "peak"},
            },
            {
                "id": 125,
                "lat": 48.2,
                "lon": 11.2,
                "tags": {"place": "village"},
            },
        ]
    }
    mock_response = MagicMock()
    mock_response.json.return_value = response
    with patch("app.providers.geo.overpass.requests.post", return_value=mock_response):
        towns = provider.get_candidate_places(
            Point(lat=48.0, lon=11.0), 10.0, "towns"
        )
        nature = provider.get_candidate_places(
            Point(lat=48.0, lon=11.0), 5.0, "nature"
        )

    assert len(towns) == 2
    assert towns[0].name == "Test Town"
    assert towns[0].place_id == "123"
    assert towns[1].name == "No Name Peak"
    assert isinstance(nature, list)


def test_overpass_query_contains_radius_center_and_tags() -> None:
    provider = OverpassProvider()
    response = {
        "elements": [
            {
                "id": 1,
                "lat": 48.0,
                "lon": 11.0,
                "tags": {"name": "Test"},
            }
        ]
    }
    mock_response = MagicMock()
    mock_response.json.return_value = response
    with patch(
        "app.providers.geo.overpass.requests.post", return_value=mock_response
    ) as mock_post:
        provider.get_candidate_places(Point(lat=48.0, lon=11.0), 10.0, "towns")

    call_args = mock_post.call_args
    assert call_args is not None
    query = call_args.kwargs["data"]["data"]
    assert "around:10000,48.0,11.0" in query
    assert "place~'town|city|village'" in query


def test_overpass_unknown_mode_defaults_to_towns() -> None:
    provider = OverpassProvider()
    mock_response = MagicMock()
    mock_response.json.return_value = {"elements": []}
    with patch(
        "app.providers.geo.overpass.requests.post", return_value=mock_response
    ) as mock_post:
        provider.get_candidate_places(Point(lat=48.0, lon=11.0), 1.0, "unknown")

    query = mock_post.call_args.kwargs["data"]["data"]
    assert "place~'town|city|village'" in query


def test_overpass_request_exception_converted_to_provider_error() -> None:
    provider = OverpassProvider()
    with patch(
        "app.providers.geo.overpass.requests.post",
        side_effect=requests.RequestException("network error"),
    ):
        with pytest.raises(ProviderError):
            provider.get_candidate_places(Point(lat=48.0, lon=11.0), 1.0, "towns")


def test_overpass_json_decode_error_converted_to_provider_error() -> None:
    provider = OverpassProvider()
    mock_response = MagicMock()
    mock_response.json.side_effect = ValueError("not json")
    with patch("app.providers.geo.overpass.requests.post", return_value=mock_response):
        with pytest.raises(ProviderError):
            provider.get_candidate_places(Point(lat=48.0, lon=11.0), 1.0, "towns")


def test_overpass_zero_radius_raises_provider_error() -> None:
    provider = OverpassProvider()
    with pytest.raises(ProviderError):
        provider.get_candidate_places(Point(lat=48.0, lon=11.0), 0.0, "towns")


def test_open_meteo_json_decode_error_converted_to_provider_error() -> None:
    provider = OpenMeteoProvider()
    mock_response = MagicMock()
    mock_response.json.side_effect = JSONDecodeError("decode error", "doc", 0)
    with patch(
        "app.providers.weather.open_meteo.requests.get", return_value=mock_response
    ):
        with pytest.raises(ProviderError):
            provider.get_hourly_forecast(Point(lat=48.0, lon=11.0), date(2024, 6, 1))


def test_open_weather_json_decode_error_converted_to_provider_error() -> None:
    provider = OpenWeatherProvider(api_key="dummy")
    mock_response = MagicMock()
    mock_response.json.side_effect = JSONDecodeError("decode error", "doc", 0)
    with patch(
        "app.providers.weather.open_weather.requests.get", return_value=mock_response
    ):
        with pytest.raises(ProviderError):
            provider.get_hourly_forecast(Point(lat=48.0, lon=11.0), date(2024, 6, 1))


def test_open_meteo_missing_required_key_raises_provider_error() -> None:
    provider = OpenMeteoProvider()
    mock_response = MagicMock()
    mock_response.json.return_value = {"hourly": {"time": ["2024-06-01T00:00"]}}
    with patch(
        "app.providers.weather.open_meteo.requests.get", return_value=mock_response
    ):
        with pytest.raises(ProviderError):
            provider.get_hourly_forecast(Point(lat=48.0, lon=11.0), date(2024, 6, 1))


def test_open_weather_missing_required_key_raises_provider_error() -> None:
    provider = OpenWeatherProvider(api_key="dummy")
    mock_response = MagicMock()
    mock_response.json.return_value = {"hourly": [{"dt": 1717200000, "temp": 15.0}]}
    with patch(
        "app.providers.weather.open_weather.requests.get", return_value=mock_response
    ):
        with pytest.raises(ProviderError):
            provider.get_hourly_forecast(Point(lat=48.0, lon=11.0), date(2024, 6, 1))


def test_open_meteo_array_length_mismatch_raises_provider_error() -> None:
    provider = OpenMeteoProvider()
    mock_response = MagicMock()
    mock_response.json.return_value = {
        "hourly": {
            "time": ["2024-06-01T00:00", "2024-06-01T01:00"],
            "temperature_2m": [15.0],
            "windspeed_10m": [5.0, 6.0],
            "precipitation": [0.0, 0.0],
            "precipitation_probability": [0, 0],
            "cloudcover": [0, 0],
        }
    }
    with patch(
        "app.providers.weather.open_meteo.requests.get", return_value=mock_response
    ):
        with pytest.raises(ProviderError):
            provider.get_hourly_forecast(Point(lat=48.0, lon=11.0), date(2024, 6, 1))


def test_open_meteo_request_params() -> None:
    provider = OpenMeteoProvider()
    target = date(2024, 6, 1)
    response = {
        "hourly": {
            "time": ["2024-06-01T00:00"],
            "temperature_2m": [15.0],
            "windspeed_10m": [5.0],
            "precipitation": [0.0],
            "precipitation_probability": [10],
            "cloudcover": [20],
        }
    }
    mock_response = MagicMock()
    mock_response.json.return_value = response
    with patch(
        "app.providers.weather.open_meteo.requests.get", return_value=mock_response
    ) as mock_get:
        provider.get_hourly_forecast(Point(lat=48.0, lon=11.0), target)

    call_args = mock_get.call_args
    assert call_args is not None
    params = call_args.kwargs["params"]
    assert params["latitude"] == 48.0
    assert params["longitude"] == 11.0
    assert params["start_date"] == "2024-06-01"
    assert params["end_date"] == "2024-06-01"
    assert params["timezone"] == "UTC"
    assert "temperature_2m" in params["hourly"]


def test_open_weather_request_params() -> None:
    provider = OpenWeatherProvider(api_key="dummy")
    target = date(2024, 6, 1)
    response = {
        "hourly": [
            {
                "dt": 1717200000,
                "temp": 15.0,
                "wind_speed": 2.0,
            }
        ]
    }
    mock_response = MagicMock()
    mock_response.json.return_value = response
    with patch(
        "app.providers.weather.open_weather.requests.get", return_value=mock_response
    ) as mock_get:
        provider.get_hourly_forecast(Point(lat=48.0, lon=11.0), target)

    call_args = mock_get.call_args
    assert call_args is not None
    params = call_args.kwargs["params"]
    assert params["lat"] == 48.0
    assert params["lon"] == 11.0
    assert params["appid"] == "dummy"
    assert params["units"] == "metric"
    assert "current,minutely,daily,alerts" in params["exclude"]

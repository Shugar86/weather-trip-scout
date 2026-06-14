from datetime import date, datetime
from unittest.mock import MagicMock

import pytest

from app.domain.models import HourlyForecastPoint, Place, Point
from app.providers.weather.base import WeatherProvider
from app.services.forecast_service import ForecastService


def _make_forecast() -> list[HourlyForecastPoint]:
    return [
        HourlyForecastPoint(
            time=datetime(2026, 6, 15, 10, 0),
            temp_c=20.0,
            wind_kmh=10.0,
            precip_mm=0.0,
            precip_probability=0.0,
            cloud_cover=20.0,
        )
    ]


def test_primary_provider_returns_forecast() -> None:
    primary = MagicMock(spec=WeatherProvider)
    primary.get_hourly_forecast.return_value = _make_forecast()
    fallback = MagicMock(spec=WeatherProvider)

    service = ForecastService(primary, fallback)
    place = Place("Test", Point(48.0, 11.0))
    result = service.get_forecast(place, date(2026, 6, 15))

    assert result == _make_forecast()
    primary.get_hourly_forecast.assert_called_once_with(place.point, date(2026, 6, 15))
    fallback.get_hourly_forecast.assert_not_called()


def test_primary_falls_back_to_fallback() -> None:
    primary = MagicMock(spec=WeatherProvider)
    primary.get_hourly_forecast.side_effect = RuntimeError("primary down")
    fallback = MagicMock(spec=WeatherProvider)
    fallback.get_hourly_forecast.return_value = _make_forecast()

    service = ForecastService(primary, fallback)
    place = Place("Test", Point(48.0, 11.0))
    result = service.get_forecast(place, date(2026, 6, 15))

    assert result == _make_forecast()
    primary.get_hourly_forecast.assert_called_once_with(place.point, date(2026, 6, 15))
    fallback.get_hourly_forecast.assert_called_once_with(place.point, date(2026, 6, 15))


def test_primary_failure_without_fallback_propagates() -> None:
    primary = MagicMock(spec=WeatherProvider)
    primary.get_hourly_forecast.side_effect = RuntimeError("primary down")

    service = ForecastService(primary, fallback=None)
    place = Place("Test", Point(48.0, 11.0))

    with pytest.raises(RuntimeError, match="primary down"):
        service.get_forecast(place, date(2026, 6, 15))

    primary.get_hourly_forecast.assert_called_once_with(place.point, date(2026, 6, 15))

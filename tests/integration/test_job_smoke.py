from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.domain.models import HourlyForecastPoint, Place, Point
from app.jobs.morning_report import MorningReportJob
from app.providers.geo.base import GeoProvider
from app.providers.maps.base import MapBuilder
from app.providers.weather.base import WeatherProvider


def _make_config():
    from app.config.loader import AppConfig

    return AppConfig(
        home={"lat": 48.0, "lon": 11.0},
        search={
            "radius_km": 100,
            "top_n_places": 2,
            "min_acceptable_score": 0,
            "mode": "towns",
        },
        time={
            "send_at_local": "07:30",
            "analyze_from": "10:00",
            "analyze_to": "18:00",
        },
        weather_preferences={
            "min_temp_c": 14,
            "max_temp_c": 24,
            "max_wind_kmh": 18,
            "max_precip_mm_per_hour": 0.3,
            "max_precip_probability": 30,
            "max_cloud_cover": 70,
            "min_good_window_hours": 3,
        },
        scoring_weights={
            "precip": 35,
            "wind": 20,
            "temp": 20,
            "cloud": 10,
            "distance": 5,
            "good_window": 10,
        },
        providers={
            "weather_primary": "open_meteo",
            "weather_fallback": "open_weather",
            "geo": "overpass",
            "map": "staticmap_osm",
        },
    )


@pytest.mark.asyncio
async def test_job_end_to_end() -> None:
    _home = Point(48.0, 11.0)
    place = Place("Test Town", Point(48.1, 11.1))

    class FakeGeoProvider(GeoProvider):
        def get_candidate_places(self, center, radius_km, mode):
            return [place]

    class FakeWeatherProvider(WeatherProvider):
        def get_hourly_forecast(self, point, target_date):
            return [
                HourlyForecastPoint(
                    time=datetime(2026, 6, 15, h, 0),
                    temp_c=20.0,
                    wind_kmh=10.0,
                    precip_mm=0.0,
                    precip_probability=0.0,
                    cloud_cover=20.0,
                )
                for h in range(10, 19)
            ]

    class FakeMapBuilder(MapBuilder):
        def build_map(self, ranked, home, radius_km):
            return None

    config = _make_config()
    settings = MagicMock()
    settings.telegram_bot_token = "token"
    settings.telegram_chat_id = "123"
    settings.open_weather_api_key = None
    settings.mapbox_token = None

    job = MorningReportJob(settings, config)

    sent_text = None

    async def fake_send_report(payload):
        nonlocal sent_text
        sent_text = payload.text

    with (
        patch.object(job, "_build_map_builder", return_value=FakeMapBuilder()),
        patch(
            "app.jobs.morning_report.CandidateService",
            return_value=MagicMock(
                find_candidates=FakeGeoProvider().get_candidate_places
            ),
        ),
        patch(
            "app.jobs.morning_report.ForecastService",
            return_value=MagicMock(
                get_forecast=FakeWeatherProvider().get_hourly_forecast
            ),
        ),
        patch(
            "app.jobs.morning_report.TelegramService",
            return_value=MagicMock(send_report=AsyncMock(side_effect=fake_send_report)),
        ),
    ):
        await job.run()

    assert sent_text is not None
    assert "Test Town" in sent_text

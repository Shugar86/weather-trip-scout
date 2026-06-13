from datetime import datetime, time

import pytest

from app.domain.models import HourlyForecastPoint, Place, Point
from app.domain.scoring import ScoringWeights, WeatherPreferences
from app.services.scoring_service import ScoringService


def _forecast(hours: list[int], **overrides) -> list[HourlyForecastPoint]:
    base = {
        "temp_c": 20.0,
        "wind_kmh": 10.0,
        "precip_mm": 0.0,
        "precip_probability": 0.0,
        "cloud_cover": 20.0,
    }
    base.update(overrides)
    return [
        HourlyForecastPoint(
            time=datetime(2026, 6, 15, h, 0),
            **base,  # type: ignore[arg-type]
        )
        for h in hours
    ]


@pytest.fixture
def prefs() -> WeatherPreferences:
    return WeatherPreferences(
        min_temp_c=14,
        max_temp_c=24,
        max_wind_kmh=18,
        max_precip_mm_per_hour=0.3,
        max_precip_probability=30,
        max_cloud_cover=70,
        min_good_window_hours=3,
    )


@pytest.fixture
def weights() -> ScoringWeights:
    return ScoringWeights(
        precip=35, wind=20, temp=20, cloud=10, distance=5, good_window=10
    )


def test_perfect_weather_scores_high(prefs: WeatherPreferences, weights: ScoringWeights) -> None:
    forecast = _forecast(list(range(10, 19)))
    place = Place("Perfect", Point(48.0, 11.0))
    service = ScoringService(prefs, weights)
    score = service.score_place(place, forecast, Point(48.0, 11.0))
    assert score.final_score >= 95
    assert score.best_time_start == time(10, 0)
    assert score.best_time_end == time(18, 0)


def test_rainy_weather_scores_low(prefs: WeatherPreferences, weights: ScoringWeights) -> None:
    forecast = _forecast(list(range(10, 19)), precip_mm=2.0)
    place = Place("Rainy", Point(48.0, 11.0))
    service = ScoringService(prefs, weights)
    score = service.score_place(place, forecast, Point(48.0, 11.0))
    assert score.final_score < 50


def test_empty_forecast_returns_zero(prefs: WeatherPreferences, weights: ScoringWeights) -> None:
    place = Place("Empty", Point(48.0, 11.0))
    service = ScoringService(prefs, weights)
    score = service.score_place(place, [], Point(48.0, 11.0))
    assert score.final_score == 0

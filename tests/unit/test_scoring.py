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


def test_perfect_weather_scores_high(
    prefs: WeatherPreferences, weights: ScoringWeights
) -> None:
    forecast = _forecast(list(range(10, 19)))
    place = Place("Perfect", Point(48.0, 11.0))
    service = ScoringService(prefs, weights)
    score = service.score_place(place, forecast, Point(48.0, 11.0))
    assert score.final_score >= 95
    assert score.best_time_start == time(10, 0)
    assert score.best_time_end == time(18, 0)


def test_rainy_weather_scores_low(
    prefs: WeatherPreferences, weights: ScoringWeights
) -> None:
    forecast = _forecast(list(range(10, 19)), precip_mm=2.0)
    place = Place("Rainy", Point(48.0, 11.0))
    service = ScoringService(prefs, weights)
    score = service.score_place(place, forecast, Point(48.0, 11.0))
    assert score.final_score < 50


def test_empty_forecast_returns_zero(
    prefs: WeatherPreferences, weights: ScoringWeights
) -> None:
    place = Place("Empty", Point(48.0, 11.0))
    service = ScoringService(prefs, weights)
    score = service.score_place(place, [], Point(48.0, 11.0))
    assert score.final_score == 0


def test_partial_good_window_detected(
    prefs: WeatherPreferences, weights: ScoringWeights
) -> None:
    forecast = _forecast(list(range(10, 19)))
    for i, hour in enumerate(forecast):
        if i < 2 or i >= 5:
            hour.wind_kmh = 30.0
    place = Place("Partial", Point(48.0, 11.0))
    service = ScoringService(prefs, weights)
    score = service.score_place(place, forecast, Point(48.0, 11.0))
    assert score.best_time_start == time(12, 0)
    assert score.best_time_end == time(14, 0)
    assert "12:00:00-14:00:00" in score.summary


def test_null_precip_probability_and_cloud_cover(
    prefs: WeatherPreferences, weights: ScoringWeights
) -> None:
    forecast = _forecast(list(range(10, 19)), precip_probability=None, cloud_cover=None)
    place = Place("NullFields", Point(48.0, 11.0))
    service = ScoringService(prefs, weights)
    score = service.score_place(place, forecast, Point(48.0, 11.0))
    assert score.final_score >= 95


def test_distance_scoring_same_vs_far(
    prefs: WeatherPreferences, weights: ScoringWeights
) -> None:
    forecast = _forecast(list(range(10, 19)))
    service = ScoringService(prefs, weights)
    same = service.score_place(
        Place("Same", Point(48.0, 11.0)), forecast, Point(48.0, 11.0)
    )
    far = service.score_place(
        Place("Far", Point(0.0, 0.0)), forecast, Point(48.0, 11.0)
    )
    assert same.final_score > far.final_score
    assert same.breakdown["distance"] == 100.0
    assert far.breakdown["distance"] < 100.0


def test_breakdown_is_populated(
    prefs: WeatherPreferences, weights: ScoringWeights
) -> None:
    forecast = _forecast(list(range(10, 19)))
    place = Place("Breakdown", Point(48.0, 11.0))
    service = ScoringService(prefs, weights)
    score = service.score_place(place, forecast, Point(48.0, 11.0))
    assert score.breakdown == {
        "weather_avg": pytest.approx(100.0),
        "distance": 100.0,
        "good_window": pytest.approx(100.0),
    }

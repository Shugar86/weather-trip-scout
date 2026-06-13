from datetime import datetime, time

from app.domain.models import HourlyForecastPoint, Place, PlaceScore, Point, ReportPayload
from app.domain.scoring import ScoringWeights, WeatherPreferences


def test_point_immutable():
    p = Point(lat=48.0, lon=11.0)
    assert p.lat == 48.0


def test_place_creation():
    place = Place(name="Munich", point=Point(48.0, 11.0))
    assert place.name == "Munich"


def test_weather_preferences_defaults():
    prefs = WeatherPreferences(
        min_temp_c=14,
        max_temp_c=24,
        max_wind_kmh=18,
        max_precip_mm_per_hour=0.3,
        max_precip_probability=30,
        max_cloud_cover=70,
        min_good_window_hours=3,
    )
    assert prefs.max_wind_kmh == 18


def test_scoring_weights_sum():
    weights = ScoringWeights(
        precip=35, wind=20, temp=20, cloud=10, distance=5, good_window=10
    )
    assert sum(weights.__dict__.values()) == 100

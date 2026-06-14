import pytest

from app.domain.scoring import ScoringWeights, WeatherPreferences


def _valid_preferences() -> WeatherPreferences:
    return WeatherPreferences(
        min_temp_c=14,
        max_temp_c=24,
        max_wind_kmh=18,
        max_precip_mm_per_hour=0.3,
        max_precip_probability=30,
        max_cloud_cover=70,
        min_good_window_hours=3,
    )


def test_min_temp_greater_than_max_temp_raises() -> None:
    with pytest.raises(ValueError, match="min_temp_c must be less than max_temp_c"):
        WeatherPreferences(
            min_temp_c=25,
            max_temp_c=24,
            max_wind_kmh=18,
            max_precip_mm_per_hour=0.3,
            max_precip_probability=30,
            max_cloud_cover=70,
            min_good_window_hours=3,
        )


def test_min_temp_equal_to_max_temp_raises() -> None:
    with pytest.raises(ValueError, match="min_temp_c must be less than max_temp_c"):
        WeatherPreferences(
            min_temp_c=20,
            max_temp_c=20,
            max_wind_kmh=18,
            max_precip_mm_per_hour=0.3,
            max_precip_probability=30,
            max_cloud_cover=70,
            min_good_window_hours=3,
        )


def test_negative_max_wind_raises() -> None:
    prefs = _valid_preferences()
    with pytest.raises(ValueError, match="max_wind_kmh must be non-negative"):
        WeatherPreferences(
            min_temp_c=prefs.min_temp_c,
            max_temp_c=prefs.max_temp_c,
            max_wind_kmh=-1,
            max_precip_mm_per_hour=prefs.max_precip_mm_per_hour,
            max_precip_probability=prefs.max_precip_probability,
            max_cloud_cover=prefs.max_cloud_cover,
            min_good_window_hours=prefs.min_good_window_hours,
        )


def test_negative_precip_mm_raises() -> None:
    prefs = _valid_preferences()
    with pytest.raises(ValueError, match="max_precip_mm_per_hour must be non-negative"):
        WeatherPreferences(
            min_temp_c=prefs.min_temp_c,
            max_temp_c=prefs.max_temp_c,
            max_wind_kmh=prefs.max_wind_kmh,
            max_precip_mm_per_hour=-0.1,
            max_precip_probability=prefs.max_precip_probability,
            max_cloud_cover=prefs.max_cloud_cover,
            min_good_window_hours=prefs.min_good_window_hours,
        )


def test_negative_precip_probability_raises() -> None:
    prefs = _valid_preferences()
    with pytest.raises(ValueError, match="max_precip_probability must be non-negative"):
        WeatherPreferences(
            min_temp_c=prefs.min_temp_c,
            max_temp_c=prefs.max_temp_c,
            max_wind_kmh=prefs.max_wind_kmh,
            max_precip_mm_per_hour=prefs.max_precip_mm_per_hour,
            max_precip_probability=-1,
            max_cloud_cover=prefs.max_cloud_cover,
            min_good_window_hours=prefs.min_good_window_hours,
        )


def test_negative_cloud_cover_raises() -> None:
    prefs = _valid_preferences()
    with pytest.raises(ValueError, match="max_cloud_cover must be non-negative"):
        WeatherPreferences(
            min_temp_c=prefs.min_temp_c,
            max_temp_c=prefs.max_temp_c,
            max_wind_kmh=prefs.max_wind_kmh,
            max_precip_mm_per_hour=prefs.max_precip_mm_per_hour,
            max_precip_probability=prefs.max_precip_probability,
            max_cloud_cover=-1,
            min_good_window_hours=prefs.min_good_window_hours,
        )


def test_zero_good_window_hours_raises() -> None:
    prefs = _valid_preferences()
    with pytest.raises(ValueError, match="min_good_window_hours must be positive"):
        WeatherPreferences(
            min_temp_c=prefs.min_temp_c,
            max_temp_c=prefs.max_temp_c,
            max_wind_kmh=prefs.max_wind_kmh,
            max_precip_mm_per_hour=prefs.max_precip_mm_per_hour,
            max_precip_probability=prefs.max_precip_probability,
            max_cloud_cover=prefs.max_cloud_cover,
            min_good_window_hours=0,
        )


def test_negative_good_window_hours_raises() -> None:
    prefs = _valid_preferences()
    with pytest.raises(ValueError, match="min_good_window_hours must be positive"):
        WeatherPreferences(
            min_temp_c=prefs.min_temp_c,
            max_temp_c=prefs.max_temp_c,
            max_wind_kmh=prefs.max_wind_kmh,
            max_precip_mm_per_hour=prefs.max_precip_mm_per_hour,
            max_precip_probability=prefs.max_precip_probability,
            max_cloud_cover=prefs.max_cloud_cover,
            min_good_window_hours=-1,
        )


@pytest.mark.parametrize(
    "field_name,value",
    [
        ("precip", -1),
        ("wind", -1),
        ("temp", -1),
        ("cloud", -1),
        ("distance", -1),
        ("good_window", -1),
    ],
)
def test_negative_scoring_weight_raises(field_name: str, value: int) -> None:
    base = {
        "precip": 1,
        "wind": 1,
        "temp": 1,
        "cloud": 1,
        "distance": 1,
        "good_window": 1,
    }
    base[field_name] = value
    with pytest.raises(ValueError, match=f"{field_name} weight must be non-negative"):
        ScoringWeights(**base)

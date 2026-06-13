import dataclasses
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config.loader import AppConfig, load_config
from app.config.settings import Settings
from app.domain.models import Place, Point
from app.domain.scoring import ScoringWeights, WeatherPreferences


def test_point_immutable() -> None:
    p = Point(lat=48.0, lon=11.0)
    assert p.lat == 48.0
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.lat = 0  # type: ignore[misc]


def test_place_creation() -> None:
    place = Place(name="Munich", point=Point(48.0, 11.0))
    assert place.name == "Munich"


def test_weather_preferences_defaults() -> None:
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


def test_scoring_weights_sum() -> None:
    weights = ScoringWeights(
        precip=35, wind=20, temp=20, cloud=10, distance=5, good_window=10
    )
    assert sum(dataclasses.asdict(weights).values()) == 100


def test_load_config_valid() -> None:
    config = load_config(Path("config.yaml"))
    assert isinstance(config, AppConfig)
    assert config.home.lat == 48.0
    assert config.home.lon == 11.0


def test_load_config_rejects_extra_key(tmp_path: Path) -> None:
    config_path = tmp_path / "config_extra.yaml"
    config_path.write_text(
        "home:\n"
        "  lat: 48.0\n"
        "  lon: 11.0\n"
        "  extra_key: bad\n"
    )
    with pytest.raises(ValidationError):
        load_config(config_path)


def test_settings_loads_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "bot-token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat-id")
    monkeypatch.setenv("OPEN_WEATHER_API_KEY", "weather-key")
    monkeypatch.setenv("MAPBOX_TOKEN", "mapbox-token")
    settings = Settings()  # type: ignore[call-arg]
    assert settings.telegram_bot_token == "bot-token"
    assert settings.telegram_chat_id == "chat-id"
    assert settings.open_weather_api_key == "weather-key"
    assert settings.mapbox_token == "mapbox-token"

from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict

from app.domain.scoring import ScoringWeights, WeatherPreferences


class HomeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    lat: float
    lon: float


class SearchConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    radius_km: float
    top_n_places: int
    min_acceptable_score: float
    mode: str


class TimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    send_at_local: str
    analyze_from: str
    analyze_to: str


class ProviderConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    weather_primary: str
    weather_fallback: str | None = None
    geo: str
    map: str


class AppConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    home: HomeConfig
    search: SearchConfig
    time: TimeConfig
    weather_preferences: WeatherPreferences
    scoring_weights: ScoringWeights
    providers: ProviderConfig


def load_config(path: Path | str = "config.yaml") -> AppConfig:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return AppConfig.model_validate(data)

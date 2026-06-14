from datetime import time
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, field_validator

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
    mode: Literal["towns", "nature"]
    max_candidates: int = 40


class TimeConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    send_at_local: time
    analyze_from: time
    analyze_to: time

    @field_validator("send_at_local", "analyze_from", "analyze_to", mode="before")
    @classmethod
    def _parse_time(cls, value: object) -> time:
        if isinstance(value, time):
            return value
        if isinstance(value, str):
            hour, minute = map(int, value.split(":"))
            return time(hour, minute)
        raise ValueError(f"invalid time value: {value!r}")


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

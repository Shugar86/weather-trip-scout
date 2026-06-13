from dataclasses import dataclass, field
from datetime import datetime, time
from typing import Any


@dataclass(frozen=True)
class Point:
    lat: float
    lon: float


@dataclass
class Place:
    name: str
    point: Point
    place_id: str | None = None
    tags: dict[str, Any] = field(default_factory=dict)


@dataclass
class HourlyForecastPoint:
    time: datetime
    temp_c: float
    wind_kmh: float
    precip_mm: float
    precip_probability: float | None
    cloud_cover: float | None


@dataclass
class PlaceScore:
    place: Place
    final_score: float
    best_time_start: time
    best_time_end: time
    summary: str
    breakdown: dict[str, float]


@dataclass
class ReportPayload:
    text: str
    image_path: str | None = None

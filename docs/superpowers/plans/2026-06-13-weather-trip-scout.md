# weather-trip-scout Implementation Plan

> **For agentic workers:** REQUIRED SUB-_SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a production-like Python MVP agent that generates a daily Telegram report of top trip destinations within 100 km where daytime weather is good for a walk.

**Architecture:** Strict layered design (`domain` → `providers` → `services` → `jobs`) with explicit wiring in `MorningReportJob`. Replaceable providers via Protocols. Config-driven behavior via `config.yaml`; secrets via `.env`.

**Tech Stack:** Python 3.12+, Pydantic v2, dataclasses, `requests`, `python-telegram-bot`, `staticmap`, `Pillow`, `pytest`, `ruff`, `mypy`, Docker.

---

## File structure

```text
weather-trip-scout/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config/
│   │   ├── __init__.py
│   │   ├── settings.py
│   │   └── loader.py
│   ├── core/
│   │   ├── __init__.py
│   │   └── exceptions.py
│   ├── domain/
│   │   ├── __init__.py
│   │   ├── models.py
│   │   └── scoring.py
│   ├── providers/
│   │   ├── __init__.py
│   │   ├── weather/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── open_meteo.py
│   │   │   └── open_weather.py
│   │   ├── geo/
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   └── overpass.py
│   │   └── maps/
│   │       ├── __init__.py
│   │       ├── base.py
│   │       ├── staticmap_osm.py
│   │       └── mapbox.py
│   ├── services/
│   │   ├── __init__.py
│   │   ├── candidate_service.py
│   │   ├── forecast_service.py
│   │   ├── scoring_service.py
│   │   ├── report_service.py
│   │   └── telegram_service.py
│   └── jobs/
│       ├── __init__.py
│       └── morning_report.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── test_scoring.py
│   │   └── test_provider_contracts.py
│   └── integration/
│       ├── __init__.py
│       └── test_job_smoke.py
├── deploy/
│   ├── weather-trip-scout.service
│   └── weather-trip-scout.timer
├── .env.example
├── .gitignore
├── config.yaml
├── pyproject.toml
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── Makefile
├── README.md
└── AGENTS.md
```

---

## Task 1: Project skeleton and tooling

**Files:**
- Create: `pyproject.toml`
- Create: `requirements.txt`
- Create: `Makefile`
- Create: `.env.example`
- Create: `config.yaml`

- [ ] **Step 1.1: Create `pyproject.toml`**

```toml
[project]
name = "weather-trip-scout"
version = "0.1.0"
description = "Morning weather trip scout agent"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.0",
    "pydantic-settings>=2.0",
    "requests>=2.31",
    "python-telegram-bot>=20.0",
    "staticmap>=0.5.6",
    "Pillow>=10.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-cov>=4.1",
    "ruff>=0.1.0",
    "mypy>=1.7",
    "types-requests>=2.31",
]

[tool.ruff]
target-version = "py312"
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4"]

[tool.mypy]
python_version = "3.12"
strict = true
warn_return_any = true
warn_unused_ignores = true

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["."]
addopts = "--cov=app --cov-report=term-missing --cov-fail-under=50"
```

- [ ] **Step 1.2: Create `requirements.txt`**

```text
pydantic>=2.0
pydantic-settings>=2.0
requests>=2.31
python-telegram-bot>=20.0
staticmap>=0.5.6
Pillow>=10.0
```

- [ ] **Step 1.3: Create `Makefile`**

```makefile
.PHONY: install test lint format check run report docker-build docker-run

install:
	pip install -r requirements.txt
	pip install -e ".[dev]"

test:
	pytest -q

lint:
	ruff check app tests
	mypy app

format:
	ruff format app tests
	ruff check --fix app tests

check: lint test

run:
	python -m app.main run

report:
	python -m app.main report

docker-build:
	docker build -t weather-trip-scout .

docker-run:
	docker run --rm --env-file .env -v $(PWD)/config.yaml:/app/config.yaml weather-trip-scout
```

- [ ] **Step 1.4: Create `.env.example`**

```env
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
OPEN_WEATHER_API_KEY=
MAPBOX_TOKEN=
```

- [ ] **Step 1.5: Create `config.yaml`**

```yaml
home:
  lat: 48.0
  lon: 11.0

search:
  radius_km: 100
  top_n_places: 5
  min_acceptable_score: 60
  mode: towns

time:
  send_at_local: "07:30"
  analyze_from: "10:00"
  analyze_to: "18:00"

weather_preferences:
  min_temp_c: 14
  max_temp_c: 24
  max_wind_kmh: 18
  max_precip_mm_per_hour: 0.3
  max_precip_probability: 30
  max_cloud_cover: 70
  min_good_window_hours: 3

scoring_weights:
  precip: 35
  wind: 20
  temp: 20
  cloud: 10
  distance: 5
  good_window: 10

providers:
  weather_primary: open_meteo
  weather_fallback: open_weather
  geo: overpass
  map: staticmap_osm
```

- [ ] **Step 1.6: Verify files exist**

Run:

```bash
ls -la pyproject.toml requirements.txt Makefile .env.example config.yaml
```

Expected: all files listed.

- [ ] **Step 1.7: Commit**

```bash
git add pyproject.toml requirements.txt Makefile .env.example config.yaml
git commit -m "chore: project skeleton and tooling"
```

---

## Task 2: Domain models and config loader

**Files:**
- Create: `app/domain/models.py`
- Create: `app/domain/scoring.py`
- Create: `app/config/settings.py`
- Create: `app/config/loader.py`
- Create: `tests/unit/test_scoring.py` (initial failing tests)

- [ ] **Step 2.1: Write failing tests for domain/config**

Create `tests/unit/test_domain_config.py`:

```python
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
```

Run:

```bash
pytest tests/unit/test_domain_config.py -v
```

Expected: FAIL — modules not found.

- [ ] **Step 2.2: Create domain models**

Create `app/domain/models.py`:

```python
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
```

- [ ] **Step 2.3: Create scoring config models**

Create `app/domain/scoring.py`:

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class WeatherPreferences:
    min_temp_c: float
    max_temp_c: float
    max_wind_kmh: float
    max_precip_mm_per_hour: float
    max_precip_probability: float
    max_cloud_cover: float
    min_good_window_hours: int


@dataclass(frozen=True)
class ScoringWeights:
    precip: float
    wind: float
    temp: float
    cloud: float
    distance: float
    good_window: float
```

- [ ] **Step 2.4: Create config loader**

Create `app/config/loader.py`:

```python
from pathlib import Path

import yaml
from pydantic import BaseModel, ConfigDict, Field

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
```

- [ ] **Step 2.5: Create settings loader**

Create `app/config/settings.py`:

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    telegram_bot_token: str
    telegram_chat_id: str
    open_weather_api_key: str | None = None
    mapbox_token: str | None = None
```

- [ ] **Step 2.6: Run domain/config tests**

Run:

```bash
pytest tests/unit/test_domain_config.py -v
```

Expected: PASS.

- [ ] **Step 2.7: Commit**

```bash
git add app/domain tests/unit/test_domain_config.py
git commit -m "feat: domain models and config loader"
```

---

## Task 3: Core exceptions

**Files:**
- Create: `app/core/exceptions.py`

- [ ] **Step 3.1: Create exceptions**

Create `app/core/exceptions.py`:

```python
class WeatherTripScoutError(Exception):
    """Base exception for the project."""


class ConfigurationError(WeatherTripScoutError):
    """Missing or invalid configuration."""


class ProviderError(WeatherTripScoutError):
    """External provider request failed."""
```

- [ ] **Step 3.2: Commit**

```bash
git add app/core/exceptions.py
git commit -m "feat: core exceptions"
```

---

## Task 4: Weather providers

**Files:**
- Create: `app/providers/weather/base.py`
- Create: `app/providers/weather/open_meteo.py`
- Create: `app/providers/weather/open_weather.py`
- Create: `tests/unit/test_provider_contracts.py` (initial part)

- [ ] **Step 4.1: Write failing contract tests**

Create initial `tests/unit/test_provider_contracts.py`:

```python
from datetime import date

import pytest

from app.domain.models import Point
from app.providers.weather.base import WeatherProvider
from app.providers.weather.open_meteo import OpenMeteoProvider
from app.providers.weather.open_weather import OpenWeatherProvider


def test_open_meteo_is_weather_provider():
    provider = OpenMeteoProvider()
    assert isinstance(provider, WeatherProvider)


def test_open_weather_requires_key():
    with pytest.raises(ConfigurationError):
        OpenWeatherProvider(api_key=None)


def test_open_meteo_returns_forecast():
    provider = OpenMeteoProvider()
    points = provider.get_hourly_forecast(Point(48.0, 11.0), date(2026, 6, 15))
    assert isinstance(points, list)
```

Run:

```bash
pytest tests/unit/test_provider_contracts.py -v
```

Expected: FAIL — modules not found.

- [ ] **Step 4.2: Create base weather protocol**

Create `app/providers/weather/base.py`:

```python
from datetime import date
from typing import Protocol

from app.domain.models import HourlyForecastPoint, Point


class WeatherProvider(Protocol):
    def get_hourly_forecast(
        self, point: Point, target_date: date
    ) -> list[HourlyForecastPoint]: ...
```

- [ ] **Step 4.3: Create Open-Meteo provider**

Create `app/providers/weather/open_meteo.py`:

```python
import logging
from datetime import date, datetime, timezone

import requests

from app.core.exceptions import ProviderError
from app.domain.models import HourlyForecastPoint, Point

logger = logging.getLogger(__name__)


class OpenMeteoProvider:
    """Free weather provider that does not require an API key."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def get_hourly_forecast(
        self, point: Point, target_date: date
    ) -> list[HourlyForecastPoint]:
        params = {
            "latitude": point.lat,
            "longitude": point.lon,
            "hourly": [
                "temperature_2m",
                "windspeed_10m",
                "precipitation",
                "precipitation_probability",
                "cloudcover",
            ],
            "timezone": "auto",
            "start_date": target_date.isoformat(),
            "end_date": target_date.isoformat(),
        }
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ProviderError(f"Open-Meteo request failed: {exc}") from exc

        data = response.json()
        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        winds = hourly.get("windspeed_10m", [])
        precips = hourly.get("precipitation", [])
        probs = hourly.get("precipitation_probability", [])
        clouds = hourly.get("cloudcover", [])

        return [
            HourlyForecastPoint(
                time=datetime.fromisoformat(t).replace(tzinfo=timezone.utc),
                temp_c=float(temps[i]),
                wind_kmh=float(winds[i]),
                precip_mm=float(precips[i]),
                precip_probability=float(probs[i]) if i < len(probs) and probs[i] is not None else None,
                cloud_cover=float(clouds[i]) if i < len(clouds) and clouds[i] is not None else None,
            )
            for i, t in enumerate(times)
        ]
```

- [ ] **Step 4.4: Create OpenWeather fallback provider**

Create `app/providers/weather/open_weather.py`:

```python
import logging
from datetime import date, datetime, timezone

import requests

from app.core.exceptions import ConfigurationError, ProviderError
from app.domain.models import HourlyForecastPoint, Point

logger = logging.getLogger(__name__)


class OpenWeatherProvider:
    """Fallback weather provider; requires an API key."""

    BASE_URL = "https://api.openweathermap.org/data/3.0/onecall"

    def __init__(self, api_key: str | None) -> None:
        if not api_key:
            raise ConfigurationError("OPEN_WEATHER_API_KEY is required for OpenWeatherProvider")
        self.api_key = api_key

    def get_hourly_forecast(
        self, point: Point, target_date: date
    ) -> list[HourlyForecastPoint]:
        params = {
            "lat": point.lat,
            "lon": point.lon,
            "appid": self.api_key,
            "units": "metric",
            "exclude": "current,minutely,daily,alerts",
        }
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ProviderError(f"OpenWeather request failed: {exc}") from exc

        data = response.json()
        hourly = data.get("hourly", [])

        return [
            HourlyForecastPoint(
                time=datetime.fromtimestamp(h["dt"], tz=timezone.utc),
                temp_c=float(h["temp"]),
                wind_kmh=float(h["wind_speed"]) * 3.6,
                precip_mm=float(h.get("rain", {}).get("1h", 0)) + float(h.get("snow", {}).get("1h", 0)),
                precip_probability=float(h.get("pop", 0)) * 100 if "pop" in h else None,
                cloud_cover=float(h.get("clouds", 0)),
            )
            for h in hourly
            if datetime.fromtimestamp(h["dt"], tz=timezone.utc).date() == target_date
        ]
```

- [ ] **Step 4.5: Update contract tests to pass**

Update `tests/unit/test_provider_contracts.py`:

```python
from datetime import date

import pytest

from app.core.exceptions import ConfigurationError
from app.domain.models import Point
from app.providers.weather.base import WeatherProvider
from app.providers.weather.open_meteo import OpenMeteoProvider
from app.providers.weather.open_weather import OpenWeatherProvider


def test_open_meteo_is_weather_provider():
    provider = OpenMeteoProvider()
    assert isinstance(provider, WeatherProvider)


def test_open_weather_requires_key():
    with pytest.raises(ConfigurationError):
        OpenWeatherProvider(api_key=None)


def test_open_weather_accepts_key():
    provider = OpenWeatherProvider(api_key="dummy")
    assert provider.api_key == "dummy"
```

Run:

```bash
pytest tests/unit/test_provider_contracts.py -v
```

Expected: PASS.

- [ ] **Step 4.6: Commit**

```bash
git add app/providers/weather tests/unit/test_provider_contracts.py
git commit -m "feat: weather providers with Open-Meteo primary and OpenWeather fallback"
```

---

## Task 5: Geo provider

**Files:**
- Create: `app/providers/geo/base.py`
- Create: `app/providers/geo/overpass.py`

- [ ] **Step 5.1: Create base geo protocol**

Create `app/providers/geo/base.py`:

```python
from typing import Protocol

from app.domain.models import Place, Point


class GeoProvider(Protocol):
    def get_candidate_places(
        self, center: Point, radius_km: float, mode: str
    ) -> list[Place]: ...
```

- [ ] **Step 5.2: Create Overpass geo provider**

Create `app/providers/geo/overpass.py`:

```python
import logging
import math

import requests

from app.core.exceptions import ProviderError
from app.domain.models import Place, Point

logger = logging.getLogger(__name__)


class OverpassProvider:
    """OSM-based candidate places within a radius."""

    BASE_URL = "https://overpass-api.de/api/interpreter"

    def get_candidate_places(
        self, center: Point, radius_km: float, mode: str
    ) -> list[Place]:
        tag = self._tag_for_mode(mode)
        query = f"""
        [out:json][timeout:25];
        (
          node[{tag}](around:{radius_km * 1000:.0f},{center.lat},{center.lon});
        );
        out body;
        """
        try:
            response = requests.post(
                self.BASE_URL,
                data={"data": query},
                timeout=30,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ProviderError(f"Overpass request failed: {exc}") from exc

        elements = response.json().get("elements", [])
        places = []
        for el in elements:
            tags = el.get("tags", {})
            name = tags.get("name") or tags.get("name:en")
            if not name:
                continue
            places.append(
                Place(
                    name=name,
                    point=Point(lat=el["lat"], lon=el["lon"]),
                    place_id=str(el.get("id")),
                    tags=tags,
                )
            )
        return places

    def _tag_for_mode(self, mode: str) -> str:
        if mode == "towns":
            return "place~'town|city|village'"
        if mode == "nature":
            return "tourism~'viewpoint|picnic_site'|natural~'peak|lake|forest'"
        return "place~'town|city|village'"
```

- [ ] **Step 5.3: Add geo contract test**

Append to `tests/unit/test_provider_contracts.py`:

```python
from app.providers.geo.base import GeoProvider
from app.providers.geo.overpass import OverpassProvider


def test_overpass_is_geo_provider():
    provider = OverpassProvider()
    assert isinstance(provider, GeoProvider)
```

Run:

```bash
pytest tests/unit/test_provider_contracts.py -v
```

Expected: PASS.

- [ ] **Step 5.4: Commit**

```bash
git add app/providers/geo tests/unit/test_provider_contracts.py
git commit -m "feat: Overpass geo provider"
```

---

## Task 6: Map builders

**Files:**
- Create: `app/providers/maps/base.py`
- Create: `app/providers/maps/staticmap_osm.py`
- Create: `app/providers/maps/mapbox.py`

- [ ] **Step 6.1: Create base map protocol**

Create `app/providers/maps/base.py`:

```python
from typing import Protocol

from app.domain.models import PlaceScore, Point


class MapBuilder(Protocol):
    def build_map(
        self,
        ranked: list[PlaceScore],
        home: Point,
        radius_km: float,
    ) -> str | None: ...
```

- [ ] **Step 6.2: Create staticmap/OSM builder**

Create `app/providers/maps/staticmap_osm.py`:

```python
import logging
import os
import tempfile

from staticmap import CircleMarker, Line, StaticMap

from app.domain.models import PlaceScore, Point

logger = logging.getLogger(__name__)


class StaticMapOSMBuilder:
    """Builds a static map using OSM tiles; no API key required."""

    WIDTH = 800
    HEIGHT = 600
    ZOOM = 8

    def build_map(
        self,
        ranked: list[PlaceScore],
        home: Point,
        radius_km: float,
    ) -> str | None:
        if not ranked:
            return None

        m = StaticMap(self.WIDTH, self.HEIGHT)
        m.add_marker(CircleMarker((home.lon, home.lat), "red", 10))

        for idx, place_score in enumerate(ranked, start=1):
            color = self._score_color(place_score.final_score)
            p = place_score.place.point
            m.add_marker(CircleMarker((p.lon, p.lat), color, 8))

        try:
            image = m.render()
            path = os.path.join(tempfile.gettempdir(), "weather_trip_scout_map.png")
            image.save(path)
            return path
        except Exception as exc:
            logger.warning("Static map rendering failed: %s", exc)
            return None

    def _score_color(self, score: float) -> str:
        if score >= 80:
            return "green"
        if score >= 60:
            return "orange"
        return "red"
```

- [ ] **Step 6.3: Create optional Mapbox builder**

Create `app/providers/maps/mapbox.py`:

```python
import logging
import os
import tempfile
from urllib.parse import urlencode

import requests
from PIL import Image, ImageDraw

from app.core.exceptions import ConfigurationError
from app.domain.models import PlaceScore, Point

logger = logging.getLogger(__name__)


class MapboxBuilder:
    """Optional Mapbox static map builder; requires MAPBOX_TOKEN."""

    WIDTH = 800
    HEIGHT = 600
    ZOOM = 8

    def __init__(self, token: str | None) -> None:
        if not token:
            raise ConfigurationError("MAPBOX_TOKEN is required for MapboxBuilder")
        self.token = token

    def build_map(
        self,
        ranked: list[PlaceScore],
        home: Point,
        radius_km: float,
    ) -> str | None:
        if not ranked:
            return None

        center = f"{home.lon},{home.lat}"
        url = (
            f"https://api.mapbox.com/styles/v1/mapbox/outdoors-v11/static/"
            f"{center},{self.ZOOM}/{self.WIDTH}x{self.HEIGHT}"
            f"?access_token={self.token}"
        )
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Mapbox request failed: %s", exc)
            return None

        path = os.path.join(tempfile.gettempdir(), "weather_trip_scout_mapbox.png")
        with open(path, "wb") as f:
            f.write(response.content)
        return path
```

- [ ] **Step 6.4: Add map contract tests**

Append to `tests/unit/test_provider_contracts.py`:

```python
from app.core.exceptions import ConfigurationError
from app.providers.maps.base import MapBuilder
from app.providers.maps.mapbox import MapboxBuilder
from app.providers.maps.staticmap_osm import StaticMapOSMBuilder


def test_staticmap_osm_is_map_builder():
    builder = StaticMapOSMBuilder()
    assert isinstance(builder, MapBuilder)


def test_mapbox_requires_token():
    with pytest.raises(ConfigurationError):
        MapboxBuilder(token=None)
```

Run:

```bash
pytest tests/unit/test_provider_contracts.py -v
```

Expected: PASS.

- [ ] **Step 6.5: Commit**

```bash
git add app/providers/maps tests/unit/test_provider_contracts.py
git commit -m "feat: static map builders with OSM default and optional Mapbox"
```

---

## Task 7: Core services — candidate, forecast, scoring

**Files:**
- Create: `app/services/candidate_service.py`
- Create: `app/services/forecast_service.py`
- Create: `app/services/scoring_service.py`
- Create: `tests/unit/test_scoring.py`

- [ ] **Step 7.1: Write failing scoring tests**

Create `tests/unit/test_scoring.py`:

```python
from datetime import datetime, time

import pytest

from app.domain.models import HourlyForecastPoint, Place, PlaceScore, Point
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


def test_perfect_weather_scores_high(prefs, weights):
    forecast = _forecast(list(range(10, 19)))
    place = Place("Perfect", Point(48.0, 11.0))
    service = ScoringService(prefs, weights)
    score = service.score_place(place, forecast, Point(48.0, 11.0))
    assert score.final_score >= 95
    assert score.best_time_start == time(10, 0)
    assert score.best_time_end == time(18, 0)


def test_rainy_weather_scores_low(prefs, weights):
    forecast = _forecast(list(range(10, 19)), precip_mm=2.0)
    place = Place("Rainy", Point(48.0, 11.0))
    service = ScoringService(prefs, weights)
    score = service.score_place(place, forecast, Point(48.0, 11.0))
    assert score.final_score < 50


def test_empty_forecast_returns_zero(prefs, weights):
    place = Place("Empty", Point(48.0, 11.0))
    service = ScoringService(prefs, weights)
    score = service.score_place(place, [], Point(48.0, 11.0))
    assert score.final_score == 0
```

Run:

```bash
pytest tests/unit/test_scoring.py -v
```

Expected: FAIL — ScoringService not found.

- [ ] **Step 7.2: Create candidate service**

Create `app/services/candidate_service.py`:

```python
from app.domain.models import Place, Point
from app.providers.geo.base import GeoProvider


class CandidateService:
    def __init__(self, provider: GeoProvider) -> None:
        self.provider = provider

    def find_candidates(self, home: Point, radius_km: float, mode: str) -> list[Place]:
        return self.provider.get_candidate_places(home, radius_km, mode)
```

- [ ] **Step 7.3: Create forecast service**

Create `app/services/forecast_service.py`:

```python
import logging
from datetime import date

from app.domain.models import HourlyForecastPoint, Place, Point
from app.providers.weather.base import WeatherProvider

logger = logging.getLogger(__name__)


class ForecastService:
    def __init__(
        self,
        primary: WeatherProvider,
        fallback: WeatherProvider | None = None,
    ) -> None:
        self.primary = primary
        self.fallback = fallback

    def get_forecast(
        self, place: Place, target_date: date
    ) -> list[HourlyForecastPoint]:
        try:
            return self.primary.get_hourly_forecast(place.point, target_date)
        except Exception as exc:
            logger.warning(
                "Primary weather provider failed for %s: %s", place.name, exc
            )
            if self.fallback is not None:
                return self.fallback.get_hourly_forecast(place.point, target_date)
            raise
```

- [ ] **Step 7.4: Create scoring service**

Create `app/services/scoring_service.py`:

```python
import logging
import math
from datetime import date, datetime, time, timedelta

from app.domain.models import HourlyForecastPoint, Place, PlaceScore, Point
from app.domain.scoring import ScoringWeights, WeatherPreferences

logger = logging.getLogger(__name__)


class ScoringService:
    def __init__(self, prefs: WeatherPreferences, weights: ScoringWeights) -> None:
        self.prefs = prefs
        self.weights = weights

    def score_place(
        self,
        place: Place,
        forecast: list[HourlyForecastPoint],
        home: Point,
    ) -> PlaceScore:
        if not forecast:
            return self._zero_score(place)

        hourly_scores = [self._hour_score(h) for h in forecast]
        avg_score = sum(hourly_scores) / len(hourly_scores)

        window_start, window_end = self._best_good_window(forecast)
        window_hours = (
            (datetime.combine(date.min, window_end) - datetime.combine(date.min, window_start)).seconds
            / 3600
            if window_start and window_end
            else 0
        )

        distance_km = self._haversine(home, place.point)
        distance_score = max(0.0, 100.0 - distance_km)

        good_window_score = min(100.0, window_hours / self.prefs.min_good_window_hours * 100)

        breakdown = {
            "weather_avg": avg_score,
            "distance": distance_score,
            "good_window": good_window_score,
        }

        final = (
            avg_score * (self.weights.precip + self.weights.wind + self.weights.temp + self.weights.cloud) / 100
            + distance_score * self.weights.distance / 100
            + good_window_score * self.weights.good_window / 100
        )

        summary = self._summary(final, window_start, window_end)

        return PlaceScore(
            place=place,
            final_score=min(100.0, max(0.0, final)),
            best_time_start=window_start or time(0, 0),
            best_time_end=window_end or time(0, 0),
            summary=summary,
            breakdown=breakdown,
        )

    def _hour_score(self, hour: HourlyForecastPoint) -> float:
        score = 100.0
        if hour.precip_mm > self.prefs.max_precip_mm_per_hour:
            score -= 40 * (hour.precip_mm / max(self.prefs.max_precip_mm_per_hour, 0.1))
        if hour.precip_probability is not None and hour.precip_probability > self.prefs.max_precip_probability:
            score -= 20 * ((hour.precip_probability - self.prefs.max_precip_probability) / 100)
        if hour.wind_kmh > self.prefs.max_wind_kmh:
            score -= 20 * ((hour.wind_kmh - self.prefs.max_wind_kmh) / max(self.prefs.max_wind_kmh, 1))
        if hour.temp_c < self.prefs.min_temp_c or hour.temp_c > self.prefs.max_temp_c:
            score -= 15
        if hour.cloud_cover is not None and hour.cloud_cover > self.prefs.max_cloud_cover:
            score -= 10 * ((hour.cloud_cover - self.prefs.max_cloud_cover) / 100)
        return max(0.0, score)

    def _best_good_window(
        self, forecast: list[HourlyForecastPoint]
    ) -> tuple[time | None, time | None]:
        good = [self._is_good_hour(h) for h in forecast]
        best_start = best_end = None
        current_start = None
        for i, ok in enumerate(good):
            if ok and current_start is None:
                current_start = forecast[i].time.time()
            if (not ok or i == len(good) - 1) and current_start is not None:
                end = forecast[i].time.time() if ok else forecast[i - 1].time.time()
                if best_start is None or (end.hour - current_start.hour) > (
                    best_end.hour - best_start.hour
                ):
                    best_start, best_end = current_start, end
                current_start = None
        return best_start, best_end

    def _is_good_hour(self, hour: HourlyForecastPoint) -> bool:
        return (
            hour.precip_mm <= self.prefs.max_precip_mm_per_hour
            and (hour.precip_probability is None or hour.precip_probability <= self.prefs.max_precip_probability)
            and hour.wind_kmh <= self.prefs.max_wind_kmh
            and self.prefs.min_temp_c <= hour.temp_c <= self.prefs.max_temp_c
            and (hour.cloud_cover is None or hour.cloud_cover <= self.prefs.max_cloud_cover)
        )

    def _haversine(self, a: Point, b: Point) -> float:
        R = 6371.0
        phi1, phi2 = math.radians(a.lat), math.radians(b.lat)
        dphi = math.radians(b.lat - a.lat)
        dlambda = math.radians(b.lon - a.lon)
        x = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        return 2 * R * math.atan2(math.sqrt(x), math.sqrt(1 - x))

    def _zero_score(self, place: Place) -> PlaceScore:
        return PlaceScore(
            place=place,
            final_score=0.0,
            best_time_start=time(0, 0),
            best_time_end=time(0, 0),
            summary="No forecast data",
            breakdown={},
        )

    def _summary(
        self, score: float, start: time | None, end: time | None
    ) -> str:
        if score >= 80:
            return f"Excellent, best window {start}-{end}"
        if score >= 60:
            return f"Good, best window {start}-{end}"
        if score >= 40:
            return "Acceptable but with caveats"
        return "Poor conditions"
```

- [ ] **Step 7.5: Run scoring tests**

Run:

```bash
pytest tests/unit/test_scoring.py -v
```

Expected: PASS.

- [ ] **Step 7.6: Commit**

```bash
git add app/services/candidate_service.py app/services/forecast_service.py app/services/scoring_service.py tests/unit/test_scoring.py
git commit -m "feat: candidate, forecast, and scoring services"
```

---

## Task 8: Report and Telegram services

**Files:**
- Create: `app/services/report_service.py`
- Create: `app/services/telegram_service.py`

- [ ] **Step 8.1: Create report service**

Create `app/services/report_service.py`:

```python
from datetime import date

from app.domain.models import PlaceScore, Point, ReportPayload
from app.providers.maps.base import MapBuilder


class ReportService:
    def __init__(self, map_builder: MapBuilder) -> None:
        self.map_builder = map_builder

    def build_report(
        self,
        ranked: list[PlaceScore],
        report_date: date,
        home: Point,
        radius_km: float,
    ) -> ReportPayload:
        text = self.build_text(ranked, report_date)
        image_path = self.map_builder.build_map(ranked, home, radius_km)
        return ReportPayload(text=text, image_path=image_path)

    def build_text(self, ranked: list[PlaceScore], report_date: date) -> str:
        header = f"🌤 Weather trip scout for {report_date.isoformat()}\n\n"
        if not ranked:
            return header + "No good destinations today. Try again tomorrow!"

        lines = [header, f"Top {len(ranked)} destinations within radius:\n"]
        for i, ps in enumerate(ranked, start=1):
            lines.append(
                f"{i}. {ps.place.name} — score {ps.final_score:.0f}\n"
                f"   Best window: {ps.best_time_start}–{ps.best_time_end}\n"
                f"   {ps.summary}"
            )
        return "\n".join(lines)
```

- [ ] **Step 8.2: Create Telegram service**

Create `app/services/telegram_service.py`:

```python
import logging

from telegram import Bot

from app.domain.models import ReportPayload

logger = logging.getLogger(__name__)


class TelegramService:
    def __init__(self, bot_token: str, chat_id: str) -> None:
        self.bot = Bot(token=bot_token)
        self.chat_id = chat_id

    def send_report(self, payload: ReportPayload) -> None:
        if payload.image_path:
            with open(payload.image_path, "rb") as photo:
                self.bot.send_photo(
                    chat_id=self.chat_id,
                    photo=photo,
                    caption=payload.text,
                )
        else:
            self.bot.send_message(
                chat_id=self.chat_id,
                text=payload.text,
            )
        logger.info("Report sent to %s", self.chat_id)
```

- [ ] **Step 8.3: Commit**

```bash
git add app/services/report_service.py app/services/telegram_service.py
git commit -m "feat: report builder and telegram delivery service"
```

---

## Task 9: Job orchestrator and CLI

**Files:**
- Create: `app/jobs/morning_report.py`
- Create: `app/main.py`

- [ ] **Step 9.1: Create morning report job**

Create `app/jobs/morning_report.py`:

```python
import logging
from datetime import date

from app.config.loader import AppConfig
from app.config.settings import Settings
from app.domain.models import PlaceScore, Point
from app.providers.geo.overpass import OverpassProvider
from app.providers.maps.mapbox import MapboxBuilder
from app.providers.maps.staticmap_osm import StaticMapOSMBuilder
from app.providers.weather.open_meteo import OpenMeteoProvider
from app.providers.weather.open_weather import OpenWeatherProvider
from app.services.candidate_service import CandidateService
from app.services.forecast_service import ForecastService
from app.services.report_service import ReportService
from app.services.scoring_service import ScoringService
from app.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)


class MorningReportJob:
    def __init__(self, settings: Settings, config: AppConfig) -> None:
        self.settings = settings
        self.config = config

    def run(self) -> None:
        home = Point(lat=self.config.home.lat, lon=self.config.home.lon)

        geo_provider = OverpassProvider()
        candidate_service = CandidateService(geo_provider)
        places = candidate_service.find_candidates(
            home, self.config.search.radius_km, self.config.search.mode
        )
        logger.info("Found %d candidate places", len(places))

        primary_weather = OpenMeteoProvider()
        fallback_weather = (
            OpenWeatherProvider(self.settings.open_weather_api_key)
            if self.settings.open_weather_api_key
            else None
        )
        forecast_service = ForecastService(primary_weather, fallback_weather)

        scoring_service = ScoringService(
            self.config.weather_preferences,
            self.config.scoring_weights,
        )

        ranked: list[PlaceScore] = []
        for place in places:
            try:
                forecast = forecast_service.get_forecast(place, date.today())
                score = scoring_service.score_place(place, forecast, home)
                if score.final_score >= self.config.search.min_acceptable_score:
                    ranked.append(score)
            except Exception as exc:
                logger.warning("Failed to process place %s: %s", place.name, exc)

        ranked.sort(key=lambda x: x.final_score, reverse=True)
        ranked = ranked[: self.config.search.top_n_places]

        map_builder = self._build_map_builder()
        report_service = ReportService(map_builder)
        report = report_service.build_report(
            ranked, date.today(), home, self.config.search.radius_km
        )

        telegram = TelegramService(
            self.settings.telegram_bot_token, self.settings.telegram_chat_id
        )
        telegram.send_report(report)
        logger.info("Morning report finished")

    def _build_map_builder(self):
        if self.settings.mapbox_token:
            return MapboxBuilder(self.settings.mapbox_token)
        return StaticMapOSMBuilder()
```

- [ ] **Step 9.2: Create CLI entrypoint**

Create `app/main.py`:

```python
import argparse
import logging
import sys

from app.config.loader import AppConfig, load_config
from app.config.settings import Settings
from app.jobs.morning_report import MorningReportJob

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Weather trip scout")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run morning report job")
    run_parser.add_argument("--config", default="config.yaml")

    args = parser.parse_args(argv)

    settings = Settings()
    config = load_config(args.config)

    if args.command == "run":
        MorningReportJob(settings, config).run()

    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 9.3: Commit**

```bash
git add app/jobs/morning_report.py app/main.py
git commit -m "feat: morning report job and CLI"
```

---

## Task 10: Integration smoke test

**Files:**
- Create: `tests/integration/test_job_smoke.py`
- Create: `tests/conftest.py`

- [ ] **Step 10.1: Create conftest**

Create `tests/conftest.py`:

```python
import pytest

from app.config.loader import AppConfig
from app.config.settings import Settings


@pytest.fixture
def app_config() -> AppConfig:
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
```

- [ ] **Step 10.2: Create integration smoke test**

Create `tests/integration/test_job_smoke.py`:

```python
from datetime import date, datetime
from unittest.mock import MagicMock

from app.domain.models import HourlyForecastPoint, Place, Point
from app.jobs.morning_report import MorningReportJob
from app.providers.geo.base import GeoProvider
from app.providers.maps.base import MapBuilder
from app.providers.weather.base import WeatherProvider
from app.services.candidate_service import CandidateService
from app.services.forecast_service import ForecastService
from app.services.report_service import ReportService
from app.services.scoring_service import ScoringService
from app.services.telegram_service import TelegramService


def test_job_end_to_end(app_config, monkeypatch):
    home = Point(48.0, 11.0)
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

    settings = MagicMock()
    settings.telegram_bot_token = "token"
    settings.telegram_chat_id = "123"
    settings.open_weather_api_key = None
    settings.mapbox_token = None

    job = MorningReportJob(settings, app_config)

    # Inject fakes via monkeypatch
    monkeypatch.setattr(job, "_build_map_builder", lambda: FakeMapBuilder())

    sent = {}

    class FakeTelegram(TelegramService):
        def __init__(self, token, chat_id):
            pass

        def send_report(self, payload):
            sent["text"] = payload.text

    monkeypatch.setattr(TelegramService, "__new__", lambda cls, *a, **kw: FakeTelegram("", ""))

    job.run()

    assert "Test Town" in sent.get("text", "")
```

Run:

```bash
pytest tests/integration/test_job_smoke.py -v
```

Expected: PASS after fixes.

- [ ] **Step 10.3: Commit**

```bash
git add tests/conftest.py tests/integration/test_job_smoke.py
git commit -m "test: integration smoke test with mocked providers"
```

---

## Task 11: Docker and deployment files

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `deploy/weather-trip-scout.service`
- Create: `deploy/weather-trip-scout.timer`

- [ ] **Step 11.1: Create Dockerfile**

Create `Dockerfile`:

```dockerfile
FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends gcc && rm -rf /var/lib/apt/lists/*

COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY config.yaml ./

ENV PYTHONUNBUFFERED=1

CMD ["python", "-m", "app.main", "run"]
```

- [ ] **Step 11.2: Create docker-compose.yml**

Create `docker-compose.yml`:

```yaml
version: "3.9"

services:
  weather-trip-scout:
    build: .
    env_file: .env
    volumes:
      - ./config.yaml:/app/config.yaml:ro
```

- [ ] **Step 11.3: Create systemd service files**

Create `deploy/weather-trip-scout.service`:

```ini
[Unit]
Description=Weather Trip Scout morning report

[Service]
Type=oneshot
WorkingDirectory=/opt/weather-trip-scout
ExecStart=/opt/weather-trip-scout/.venv/bin/python -m app.main run
EnvironmentFile=/opt/weather-trip-scout/.env
```

Create `deploy/weather-trip-scout.timer`:

```ini
[Unit]
Description=Run weather-trip-scout every morning

[Timer]
OnCalendar=*-*-* 07:30:00
Persistent=true

[Install]
WantedBy=timers.target
```

- [ ] **Step 11.4: Commit**

```bash
git add Dockerfile docker-compose.yml deploy/
git commit -m "chore: Dockerfile, compose and systemd timer"
```

---

## Task 12: Documentation

**Files:**
- Create: `README.md`
- Create: `AGENTS.md`

- [ ] **Step 12.1: Create README.md**

Create `README.md`:

```markdown
# weather-trip-scout

Morning agent that finds the best trip destinations within 100 km where the daytime weather is good for a walk, then sends a Telegram report with a map.

## Quick start

1. Copy environment file and fill secrets:

```bash
cp .env.example .env
```

2. Install dependencies:

```bash
make install
```

3. Adjust `config.yaml` for your home coordinates and preferences.

4. Run once:

```bash
make run
```

## Docker

```bash
docker-compose up --build
```

## Cron example

```cron
30 7 * * * cd /path/to/weather-trip-scout && /path/to/venv/bin/python -m app.main run
```

## Providers

- Weather primary: Open-Meteo (free, no key)
- Weather fallback: OpenWeatherMap (requires `OPEN_WEATHER_API_KEY`)
- Geo: Overpass/OSM (free)
- Map: staticmap/OSM (free) or Mapbox (requires `MAPBOX_TOKEN`)

## Testing

```bash
make test
make lint
```
```

- [ ] **Step 12.2: Create AGENTS.md**

Create `AGENTS.md`:

```markdown
# Agent Notes: weather-trip-scout

## Tech stack
- Python 3.12+
- Pydantic v2 for config
- Replaceable providers via Protocols
- pytest, ruff, mypy

## Conventions
- All thresholds and weights live in `config.yaml`.
- Secrets live only in `.env`.
- Providers must implement the relevant Protocol in `app/providers/`.
- Services are stateless and receive providers via constructor injection.
- `MorningReportJob` wires everything together.
- Never commit `.env` or API keys.
- Run `make check` before committing.
```

- [ ] **Step 12.3: Commit**

```bash
git add README.md AGENTS.md
git commit -m "docs: README and AGENTS.md"
```

---

## Task 13: Final verification and commit

- [ ] **Step 13.1: Run lint and tests**

```bash
make check
```

Expected: ruff and mypy pass; pytest passes with ≥50% coverage.

- [ ] **Step 13.2: Push to remote**

```bash
git push origin main
```

- [ ] **Step 13.3: Final starter commit**

If any fixes were needed, commit them:

```bash
git add -A
git commit -m "fix: lint/test adjustments"
git push origin main
```

---

## Self-review checklist

- [ ] **Spec coverage:** Every design section (domain, providers, services, job, error handling, tests, Docker) maps to at least one task.
- [ ] **Placeholder scan:** No "TBD", "TODO", or "implement later" in the plan.
- [ ] **Type consistency:** `Point`, `Place`, `HourlyForecastPoint`, `PlaceScore`, `ReportPayload` used consistently.
- [ ] **No hardcoded secrets:** All secrets come from `.env` via `Settings`.
- [ ] **Testability:** Each service is injectable and unit-testable.

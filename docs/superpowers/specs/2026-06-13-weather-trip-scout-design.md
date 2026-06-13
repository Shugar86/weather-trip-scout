# Design Doc: weather-trip-scout

**Date:** 2026-06-13  
**Status:** Approved  
**Source prompt:** `/home/shugar/Downloads/weather-trip-scout-coder-prompt.md`

## Purpose

Production-like MVP Python-агента, который каждое утро автоматически формирует Telegram-отчёт: куда можно поехать в радиусе 100 км от домашней точки, чтобы днём была хорошая погода для прогулки.

## Decisions made

| Question | Decision |
|---|---|
| Provider stack | **Hybrid:** Open-Meteo (primary weather), OpenWeatherMap (fallback weather, only if API key provided), Nominatim/OSM (geo), staticmap/OSM (default map), optional Mapbox (if token provided). |
| Architecture style | **Strict layered** (`domain` → `providers` → `services` → `jobs`), explicit wiring in `MorningReportJob`. |
| Deployment | Local + Docker. Cron runs on host or inside container. Optional systemd timer unit in `deploy/`. |
| Python stack | Python 3.12+, Pydantic v2, dataclasses, `requests`, `python-telegram-bot` (or raw Bot API via `requests`), `staticmap`, `Pillow`. |
| Quality | `ruff`, `mypy --strict`, `pytest`, `Makefile`. |

## Folder structure

```text
weather-trip-scout/
├── app/
│   ├── config/
│   │   ├── settings.py          # Pydantic Settings, .env + config.yaml
│   │   └── loader.py            # загрузка config.yaml
│   ├── domain/
│   │   ├── models.py            # Place, HourlyForecastPoint, PlaceScore, ...
│   │   └── scoring.py           # WeatherPreferences, ScoringWeights
│   ├── providers/
│   │   ├── weather/
│   │   │   ├── base.py          # WeatherProvider Protocol
│   │   │   ├── open_meteo.py    # primary: free, no key
│   │   │   └── open_weather.py  # fallback: only if key is set
│   │   ├── geo/
│   │   │   ├── base.py          # GeoProvider Protocol
│   │   │   └── nominatim.py     # OSM towns/places in radius
│   │   └── maps/
│   │       ├── base.py          # MapBuilder Protocol
│   │       ├── staticmap_osm.py # staticmap + OSM tiles
│   │       └── mapbox.py        # optional, if MAPBOX_TOKEN
│   ├── services/
│   │   ├── candidate_service.py
│   │   ├── forecast_service.py
│   │   ├── scoring_service.py
│   │   ├── report_service.py    # text + map call
│   │   └── telegram_service.py
│   ├── jobs/
│   │   └── morning_report.py    # orchestrator
│   └── main.py                  # CLI entrypoint: run, report
├── tests/
│   ├── unit/
│   │   ├── test_scoring.py
│   │   └── test_provider_contracts.py
│   ├── integration/
│   │   └── test_job_smoke.py
│   └── conftest.py
├── deploy/
│   └── weather-trip-scout.timer # optional systemd timer
├── .env.example
├── config.yaml
├── requirements.txt
├── pyproject.toml
├── Dockerfile
├── Makefile
├── README.md
└── AGENTS.md
```

## Domain models

Core dataclasses in `app/domain/models.py`:

- `Point` — lat/lon value object.
- `Place` — name, point, optional id, tags.
- `HourlyForecastPoint` — hourly weather snapshot.
- `PlaceScore` — place + final score + best time window + summary + score breakdown.
- `ReportPayload` — text + optional image path.

Config models in `app/domain/scoring.py` and `app/config/`:

- `WeatherPreferences` — thresholds from `config.yaml`.
- `ScoringWeights` — factor weights.
- `AppConfig` — full `config.yaml` as Pydantic with `extra="forbid"`.
- `Settings` — Pydantic Settings for `.env` secrets.

## Protocols

```python
class WeatherProvider(Protocol):
    def get_hourly_forecast(
        self, point: Point, date: date
    ) -> list[HourlyForecastPoint]: ...

class GeoProvider(Protocol):
    def get_candidate_places(
        self, center: Point, radius_km: float, mode: str
    ) -> list[Place]: ...

class MapBuilder(Protocol):
    def build_map(
        self,
        ranked: list[PlaceScore],
        home: Point,
        radius_km: float,
    ) -> str | None: ...

class TelegramDelivery(Protocol):
    def send_report(
        self, chat_id: str, text: str, image_path: str | None
    ) -> None: ...
```

## Services

- `CandidateService` — fetches candidate places via `GeoProvider`.
- `ForecastService` — fetches hourly forecast per place; tries primary provider, falls back to secondary on `ProviderError`.
- `ScoringService` — computes `PlaceScore` using weights and thresholds; finds best continuous good-weather window inside 10:00–18:00.
- `ReportService` — builds text summary and delegates map generation to `MapBuilder`; returns `ReportPayload`.
- `TelegramService` — sends text + optional photo to Telegram chat.

## Job orchestration

`MorningReportJob.run()`:

1. Load `Settings` + `AppConfig`.
2. Build provider instances.
3. Fetch candidate places.
4. For each place:
   - fetch forecast (with fallback);
   - on any provider error log warning and skip place;
   - score place.
5. Filter by `min_acceptable_score`.
6. Sort by `final_score` desc, take `top_n`.
7. Build text summary.
8. Build static map (fallback to text-only if map fails).
9. Send via Telegram.
10. Log outcome.

## Data flow

```
cron/systemd timer
        ↓
python -m app.main run
        ↓
MorningReportJob.run()
        ↓
Settings + AppConfig
        ↓
GeoProvider.get_candidate_places(home, 100km)
        ↓
for each place:
    ForecastService.get_forecast(place.point, today)
        ↓ (fallback on primary error)
ScoringService.score(place, forecast, prefs)
        ↓
filter(score ≥ min_acceptable_score)
        ↓
sort by final_score desc → top_n
        ↓
ReportService.build_text(ranked, today)
        ↓
MapBuilder.build_map(ranked, home, radius)
        ↓ (fallback: None)
TelegramService.send_report(chat_id, text, image_path?)
        ↓
log result
```

## Error handling

| Scenario | Behavior |
|---|---|
| Single place fails | Log warning, skip place, continue job. |
| Primary weather provider fails | Log error, try fallback provider if configured. |
| Fallback weather provider fails | Log critical, skip place. |
| Map build fails | Log warning, send text-only report. |
| No places above threshold | Send honest "no good destinations today" message. |
| Telegram API fails | Log critical, exit with non-zero code. |
| Missing required secret | Raise `ConfigurationError` at startup with clear message. |

Principles:

- Only catch specific exceptions; never use bare `except:`.
- Services return results; expected failures (e.g. map unavailable) return `None` or skip, not exceptions.
- Custom exceptions live in `app/core/exceptions.py`: `WeatherTripScoutError`, `ConfigurationError`, `ProviderError`.

## Scoring logic

For each place inside the analysis window 10:00–18:00:

1. Per-hour penalties for:
   - precipitation mm/h > threshold;
   - precipitation probability > threshold (if available);
   - wind km/h > threshold;
   - temp outside [min, max];
   - cloud cover > threshold.
2. Find the longest continuous window where all hourly thresholds pass.
3. Compute sub-scores:
   - precip score;
   - wind score;
   - temp score;
   - cloud score;
   - distance score (closer to home is better);
   - good-window score (longer window is better, requires ≥ `min_good_window_hours`).
4. Weighted sum → `final_score` (0–100).
5. Return `best_time_start`, `best_time_end`, summary, breakdown.

All thresholds and weights come from `config.yaml`.

## Testing

- `tests/unit/test_scoring.py` — scoring behavior with synthetic forecasts.
- `tests/unit/test_provider_contracts.py` — protocol conformance and config errors.
- `tests/integration/test_job_smoke.py` — end-to-end with in-memory mock providers.
- `Makefile` targets: `test`, `lint`, `format`.

## Deployment

- `Dockerfile` based on `python:3.12-slim`.
- `docker-compose.yml` optional for local run.
- `deploy/weather-trip-scout.timer` + `.service` for systemd.
- Cron example in `README.md`.
- No secrets in repo; `.env.example` committed, `.env` ignored.

## Out of scope

- Multi-user / multi-home support.
- Interactive Telegram bot commands beyond a stub `/report` handler.
- Real-time weather updates or subscriptions.
- Web UI.

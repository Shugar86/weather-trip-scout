# Changelog

Все значимые изменения в проекте фиксируются в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
и этот проект придерживается [Semantic Versioning](https://semver.org/lang/ru/).

## [Unreleased]

### Added
- Полированная документация: README, AGENTS.md, CONTRIBUTING.md, CHANGELOG.md.

## [0.1.0] — 2026-06-13

### Added
- CLI-точка входа `python -m app.main run|report`.
- `MorningReportJob` — связывает сервисы в единый сценарий утреннего отчёта.
- `CandidateService` + Overpass-провайдер для поиска мест в радиусе до 100 км.
- `ForecastService` + Open-Meteo (primary) и OpenWeatherMap (fallback) провайдеры погоды.
- `ScoringService` — оценка мест по температуре, осадкам, ветру, облачности, расстоянию и «хорошему окну».
- `ReportService` и `TelegramService` — сборка и отправка отчёта в Telegram.
- Статические карты: `staticmap_osm` по умолчанию, `mapbox` — опционально.
- Конфигурация через `config.yaml` и `.env` с Pydantic v2.
- Makefile с командами `install`, `run`, `report`, `test`, `lint`, `format`, `check`.
- Docker и docker-compose окружение.
- systemd unit и timer в `deploy/`.
- Unit и интеграционные тесты (pytest + coverage).
- README, AGENTS.md, LICENSE, CONTRIBUTING, CHANGELOG.

### Fixed
- Обработка ошибок провайдеров с fallback и пропуском «битого» места.
- Безопасный Dockerfile с непривилегированным пользователем.

[Unreleased]: https://github.com/Shugar86/weather-trip-scout/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/Shugar86/weather-trip-scout/releases/tag/v0.1.0

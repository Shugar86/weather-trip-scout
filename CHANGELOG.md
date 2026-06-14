# Changelog

Все значимые изменения в проекте фиксируются в этом файле.

Формат основан на [Keep a Changelog](https://keepachangelog.com/ru/1.1.0/),
и этот проект придерживается [Semantic Versioning](https://semver.org/lang/ru/).

## [Unreleased]

### Added
- Режим `--dry-run` для команд `run`/`report`: полный пайплайн с выводом отчёта в stdout без отправки в Telegram (и без необходимости в токене бота).
- Ограничение `search.max_candidates` (по умолчанию 40): берём ближайшие места, чтобы не делать сотни запросов погоды.
- Полированная документация: README, AGENTS.md, CONTRIBUTING.md, CHANGELOG.md.

### Fixed
- Overpass возвращал `406 Not Acceptable` на дефолтный User-Agent `python-requests` — теперь шлём собственный User-Agent, гео-поиск снова работает.
- Отсутствие ключа OpenWeatherMap больше не роняет запуск: недоступный платный fallback пропускается, основной бесплатный провайдер Open-Meteo продолжает работать.

### Changed
- `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID` теперь опциональны и проверяются только при реальной отправке отчёта.

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

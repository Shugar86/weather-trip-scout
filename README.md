# Weather Trip Scout

> Тихий утренний советчик: находит лучшие направления для поездки в радиусе до 100 км и присылает в Telegram прогноз с картой.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Ruff](https://img.shields.io/badge/linter-ruff-green.svg)](https://docs.astral.sh/ruff/)
[![Mypy](https://img.shields.io/badge/types-mypy-blue.svg)](https://mypy-lang.org/)
[![pytest](https://img.shields.io/badge/tests-pytest-blue.svg)](https://docs.pytest.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg)](./LICENSE)

---

## Что это

Weather Trip Scout — это небольшой Python-агент, который берёт на себя рутину «а куда бы съездить сегодня?». Каждое утро он сам смотрит погоду вокруг домашней точки, оценивает города, деревни и природные объекты по температуре, осадкам, ветру и облачности, а затем присылает в Telegram короткий отчёт: куда стоит поехать, во сколько лучше выезжать и почему.

Если хороших направлений нет — он честно скажет об этом и не выдумает «почти хорошую» погоду.

### Для кого

- Для тех, кто живёт в городе и хочет выбираться на природу или в соседние города по выходным.
- Для владельцев дачи/дома, которым важен прогноз на день в радиусе поездки.
- Для любителей автоматизации, кому нравится получать один аккуратный отчёт вместо бесконечного свайпинга по погодным приложениям.

---

## Возможности

- **Поиск мест** в радиусе до 100 км через Overpass API / OpenStreetMap.
- **Прогноз погоды** на сегодня от Open-Meteo (без ключа) с fallback на OpenWeatherMap.
- **Умный скоринг** мест по температуре, осадкам, ветру, облачности, расстоянию и длине «хорошего окна».
- **Статическая карта** PNG с домом, радиусом и маркерами топ-мест (OSM бесплатно; Mapbox — опционально).
- **Telegram-отчёт** текстом + изображением карты.
- **Гибкая конфигурация** через `config.yaml`: координаты дома, пороги погоды, веса факторов, провайдеры.
- **Запуск по расписанию** через cron / systemd timer или вручную.
- **Docker-окружение** «из коробки».

---

## Быстрый старт

### 1. Переменные окружения

```bash
cp .env.example .env
```

Открой `.env` и заполни:

| Переменная | Обязательная | Описание |
|---|---|---|
| `TELEGRAM_BOT_TOKEN` | да | Токен бота от [@BotFather](https://t.me/BotFather) |
| `TELEGRAM_CHAT_ID` | да | ID чата или канала для отчётов |
| `OPEN_WEATHER_API_KEY` | нет | Ключ [OpenWeatherMap](https://openweathermap.org/api) для fallback |
| `MAPBOX_TOKEN` | нет | Токен [Mapbox](https://docs.mapbox.com/help/getting-started/access-tokens/) для альтернативной карты |

### 2. Окружение и зависимости

```bash
python3 -m venv .venv
source .venv/bin/activate

make install
# или: pip install -r requirements.txt && pip install -e ".[dev]"
```

### 3. Конфигурация

Отредактируй `config.yaml`:

```yaml
home:
  lat: 48.1351   # твои координаты
  lon: 11.5820

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

### 4. Запуск

Разовый отчёт:

```bash
make run
# или: python -m app.main run
```

Алиас с тем же смыслом:

```bash
make report
# или: python -m app.main report
```

---

## Docker

```bash
docker compose up --build
```

Для локального разового запуска с остановкой после выполнения:

```bash
docker compose up --build --abort-on-container-exit
```

Compose поднимает сервис `weather-trip-scout`, читает секреты из `.env` и монтирует `config.yaml` в режиме read-only.

---

## Расписание

### cron

```cron
30 7 * * * cd /path/to/weather-trip-scout && /path/to/.venv/bin/python -m app.main run >> /tmp/weather-trip-scout.log 2>&1
```

### systemd

```bash
sudo cp deploy/weather-trip-scout.service /etc/systemd/system/
sudo cp deploy/weather-trip-scout.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now weather-trip-scout.timer
```

---

## Архитектура и стек

| Область | Технология |
|---------|------------|
| Язык | Python 3.12+ |
| Конфигурация | Pydantic v2, pydantic-settings, PyYAML |
| Погода | Open-Meteo (primary), OpenWeatherMap (fallback) |
| Гео-поиск | Overpass API / OpenStreetMap |
| Карты | `staticmap` + OSM; Mapbox — опционально |
| Telegram | `python-telegram-bot` |
| Качество кода | pytest, pytest-cov, pytest-asyncio, ruff, mypy |
| Автоматизация | Makefile, Docker, systemd |

### Структура проекта

```text
weather-trip-scout/
├── app/
│   ├── config/           # Pydantic-модели для config.yaml и .env
│   ├── core/             # Базовые исключения
│   ├── domain/           # Чистые dataclass-модели и scoring-конфиг
│   ├── providers/        # Protocol-based адаптеры
│   │   ├── weather/      # Open-Meteo, OpenWeatherMap
│   │   ├── geo/          # Overpass / OSM
│   │   └── maps/         # staticmap+OSM, Mapbox
│   ├── services/         # Stateless бизнес-логика
│   ├── jobs/             # Сценарии запуска
│   └── main.py           # CLI entrypoint
├── deploy/               # systemd unit и timer
├── tests/                # unit + интеграционные тесты
├── config.yaml           # Пользовательская конфигурация
├── pyproject.toml        # Метаданные и настройки инструментов
├── Makefile              # Стандартные команды
├── Dockerfile
└── docker-compose.yml
```

### Принципы

- **Domain** не зависит от внешнего мира.
- **Providers** реализуют `Protocol` и легко заменяются.
- **Services** stateless, получают провайдеры через конструктор.
- **Jobs** связывают сервисы в единый сценарий.
- **Config** управляет поведением: провайдеры выбираются по имени через `app/providers/factory.py`.

---

## Провайдеры

| Провайдер | Назначение | Ключ API | Fallback |
|---|---|---|---|
| **Open-Meteo** | Почасовой прогноз | не нужен | — |
| **OpenWeatherMap** | Почасовой прогноз | `OPEN_WEATHER_API_KEY` | Open-Meteo |
| **Overpass / OSM** | Поиск городов и объектов | не нужен | — |
| **staticmap + OSM** | Статическая карта | не нужен | — |
| **Mapbox** | Статическая карта | `MAPBOX_TOKEN` | staticmap+OSM |

---

## Тесты и качество кода

Все команды запускаются внутри активированного виртуального окружения.

```bash
make test        # pytest с coverage
make lint        # ruff + mypy
make format      # ruff format + auto-fix
make check       # lint + test
```

Состояние проекта:

- 55+ тестов, покрытие ~85%.
- `mypy --strict` — без ошибок.
- `ruff check app tests` — чисто.

---

## Характер проекта

Вайб: **calm** — «тихий утренний советчик».

1. **Честность прежде всего.** Нет хороших направлений — скажем об этом прямо.
2. **Никакого хайпа.** Никаких «ЛУЧШИЙ ДЕНЬ ДЛЯ ПОЕЗДКИ!!!» — только факты, оценки и карта.
3. **Бережное отношение к данным.** Работаем с бесплатными API по умолчанию; fallback включается только при наличии ключа.

---

## Лицензия

[MIT](./LICENSE) — см. файл `LICENSE`.

---

## Участие и история изменений

- [CONTRIBUTING.md](./CONTRIBUTING.md) — как поучаствовать.
- [CHANGELOG.md](./CHANGELOG.md) — что нового.

---

## Известные ограничения и roadmap

- `app/main.py` пока не покрыт тестами.
- Временные PNG-файлы карт не удаляются автоматически после отправки.
- `MapboxBuilder` показывает только центр карты без маркеров мест; полноценная карта доступна через `staticmap_osm`.
- `send_at_local` в конфиге задаёт целевое время, но реальный запуск управляется cron / systemd.

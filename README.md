# Weather Trip Scout

Асинхронный Python-агент, который каждое утро анализирует погоду в радиусе до 100 км от дома и присылает в Telegram подборку лучших направлений для поездки с картой и прогнозом.

[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/)
[![Ruff](https://img.shields.io/badge/linter-ruff-green.svg)](https://docs.astral.sh/ruff/)
[![Mypy](https://img.shields.io/badge/types-mypy-blue.svg)](https://mypy-lang.org/)
[![pytest](https://img.shields.io/badge/tests-pytest-blue.svg)](https://docs.pytest.org/)

---

## Что делает

Каждый день в заданное время (через cron / systemd timer) или по ручной команде:

1. **Находит кандидатов** — города, деревни, природные объекты в радиусе `search.radius_km` км от дома через Overpass API (OpenStreetMap).
2. **Забирает прогноз** — почасовая погода на сегодня от Open-Meteo; при сбое переключается на OpenWeatherMap (если задан ключ).
3. **Оценивает места** по температуре, осадкам, вероятности дождя, ветру, облачности, расстоянию и длине непрерывного «хорошего окна» в заданном диапазоне времени.
4. **Выбирает топ** — до `search.top_n_places` мест с оценкой не ниже `search.min_acceptable_score`.
5. **Строит карту** — статическая PNG с домом, радиусом и маркерами лучших мест (OSM бесплатно; Mapbox — опционально).
6. **Отправляет отчёт** — текст + карта в Telegram-чат или канал.

Если хороших направлений нет, агент честно сообщит об этом.

---

## Быстрый старт

### 1. Переменные окружения

```bash
cp .env.example .env
```

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
# или: pip install -r requirements.txt
```

### 3. Конфигурация

Отредактируйте `config.yaml`:

```yaml
home:
  lat: 48.1351   # ваши координаты
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

Ручной отчёт (алиас):

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

## Архитектура

```text
app/
├── config/           # Pydantic-модели для config.yaml и .env
├── core/             # Базовые исключения
├── domain/           # Чистые dataclass-модели и scoring-конфиг
├── providers/        # Protocol-based адаптеры
│   ├── weather/      # Open-Meteo (primary), OpenWeatherMap (fallback)
│   ├── geo/          # Overpass / OSM
│   └── maps/         # staticmap+OSM (default), Mapbox (optional)
├── services/         # Stateless бизнес-логика
│   ├── candidate_service.py
│   ├── forecast_service.py
│   ├── scoring_service.py
│   ├── report_service.py
│   └── telegram_service.py
├── jobs/             # Сценарии запуска
│   └── morning_report.py
└── main.py           # CLI entrypoint
```

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

Состояние на момент релиза:

- **55 тестов**, покрытие ~85%
- `mypy --strict` — без ошибок
- `ruff check app tests` — чисто

---

## Лицензия

MIT — см. [LICENSE](./LICENSE) (если файл добавлен).

---

## Roadmap / известные ограничения

- `app/main.py` пока не покрыт тестами.
- Временные PNG-файлы карт не удаляются автоматически после отправки.
- `MapboxBuilder` показывает только центр карты без маркеров мест; полноценная карта доступна через `staticmap_osm`.
- `send_at_local` в конфиге задаёт целевое время, но реальный запуск управляется cron / systemd.

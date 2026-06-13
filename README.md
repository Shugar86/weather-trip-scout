# Weather Trip Scout

Утренний Telegram-бот, который ищет лучшие направления для поездки на день в заданном радиусе от дома и присылает сводку с погодой, баллами и картой.

## Что делает

Каждое утро (или по команде) бот:

1. Находит города и достопримечательности в радиусе до `search.radius_km` км от домашних координат.
2. Запрашивает почасовой прогноз погоды.
3. Оценивает каждое место по температуре, осадкам, ветру, облачности и расстоянию.
4. Выбирает топ `search.top_n_places` мест с оценкой не ниже `search.min_acceptable_score`.
5. Строит карту маршрута и отправляет отчёт в Telegram.

## Быстрый старт

1. Скопируйте пример переменных окружения и заполните секреты:

   ```bash
   cp .env.example .env
   ```

   Обязательные: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`.  
   Опциональные: `OPEN_WEATHER_API_KEY`, `MAPBOX_TOKEN`.

2. Создайте и активируйте виртуальное окружение (команды `make` и инструменты ниже запускайте внутри него):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. Установите зависимости:

   ```bash
   make install
   # или
   pip3 install -r requirements.txt
   ```

4. Настройте `config.yaml`: укажите домашние координаты, радиус поиска, время отправки и предпочтения по погоде.

5. Запустите разовый отчёт:

   ```bash
   make run
   # или
   python3 -m app.main run
   ```

## Docker

```bash
docker compose up --build
```

`docker-compose.yml` монтирует `config.yaml` и читает секреты из `.env`.

> Для локального разового запуска используйте:
>
> ```bash
> docker compose up --build --abort-on-container-exit
> ```

## Cron

Ежедневное выполнение в 7:30 по местному времени (пример для crontab):

```cron
30 7 * * * cd /path/to/weather-trip-scout && /usr/bin/docker compose up --build --abort-on-container-exit >> /tmp/weather-trip-scout.log 2>&1
```

Или без Docker:

```cron
30 7 * * * cd /path/to/weather-trip-scout && /path/to/.venv/bin/python -m app.main run >> /tmp/weather-trip-scout.log 2>&1
```

## Провайдеры

| Провайдер | Назначение | Ключ API |
|-----------|-----------|----------|
| **Open-Meteo** | Основной прогноз погоды | Не нужен |
| **OpenWeatherMap** | Резервный прогноз погоды | `OPEN_WEATHER_API_KEY` |
| **Overpass / OSM** | Поиск городов и достопримечательностей | Не нужен |
| **staticmap + OSM** | Генерация карты | Не нужен |
| **Mapbox** | Альтернативная генерация карты | `MAPBOX_TOKEN` |

Open-Meteo, Overpass, staticmap и OSM — бесплатные и не требуют регистрации.

## Тесты и линтеры

```bash
make test
make lint
make check      # lint + test
make format
```

## Архитектура

```text
app/
├── config/           # Загрузка config.yaml и переменных окружения
├── domain/           # Модели (Place, Forecast, PlaceScore) и расчёт скоринга
├── providers/        # Реализации протоколов погоды, гео и карт
│   ├── weather/
│   ├── geo/
│   └── maps/
├── services/         # Stateless бизнес-логика (кандидаты, прогноз, скоринг, отчёт, Telegram)
└── jobs/             # Сценарии запуска (MorningReportJob)
```

- Провайдеры реализуют `Protocol` из `base.py`.
- Сервисы не хранят состояния, их можно легко тестировать и подменять.
- `MorningReportJob` связывает всё воедино: находит места, получает прогноз, считает баллы, строит отчёт и отправляет.

# AGENTS.md

## Стек

- Python 3.12+
- Pydantic 2 / pydantic-settings
- python-telegram-bot
- requests, staticmap, Pillow, pyyaml
- pytest, pytest-cov, pytest-asyncio, ruff, mypy

## Соглашения

- **Конфигурация** приложения — в `config.yaml` (координаты, радиус, предпочтения, провайдеры).
- **Секреты** — только в `.env`. Никогда не коммитить `.env`, API-ключи и токены.
- **Провайдеры** реализуют `Protocol` из `providers/<area>/base.py`.
- **Сервисы** stateless, принимают провайдеры через конструктор и возвращают доменные модели.
- **Job** (`jobs/morning_report.py`) связывает сервисы и провайдеры в единый сценарий.
- Типизация строгая: `mypy --strict`.

## Команды

Все команды ниже выполняйте внутри виртуального окружения (например, после `source .venv/bin/activate`).

```bash
make install    # установить зависимости (pip3)
make run        # одиночный отчёт
make report     # то же самое
make test       # pytest + coverage
make lint       # ruff + mypy
make check      # lint + test
make format     # ruff format и автофикс
```

## Перед коммитом

1. Запустить `make check`.
2. Убедиться, что `.env` и ключи не попали в индекс.
3. Обновить `README.md` / `AGENTS.md`, если меняли архитектуру, конфиг или команды.

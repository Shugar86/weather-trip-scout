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
	docker run --rm --env-file .env -v $(CURDIR)/config.yaml:/app/config.yaml weather-trip-scout

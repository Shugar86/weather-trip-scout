from unittest.mock import AsyncMock, patch

import pytest
from pydantic import ValidationError

from app.config.loader import AppConfig
from app.core.exceptions import WeatherTripScoutError
from app.jobs.morning_report import MorningReportJob
from app.main import main


def _make_config() -> AppConfig:
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


def test_run_command_executes_job(tmp_path) -> None:
    config_path = tmp_path / "test_config.yaml"
    config_path.write_text("")

    mock_job_run = AsyncMock()

    with (
        patch("app.main.Settings") as mock_settings,
        patch("app.main.load_config", return_value=_make_config()) as mock_load_config,
        patch.object(MorningReportJob, "run", mock_job_run),
    ):
        result = main(["run", "--config", str(config_path)])

    assert result == 0
    mock_settings.assert_called_once_with()
    mock_load_config.assert_called_once_with(str(config_path))
    mock_job_run.assert_awaited_once()


def test_default_config_path_is_config_yaml() -> None:
    mock_job_run = AsyncMock()

    with (
        patch("app.main.Settings"),
        patch("app.main.load_config", return_value=_make_config()) as mock_load_config,
        patch.object(MorningReportJob, "run", mock_job_run),
    ):
        main(["run"])

    mock_load_config.assert_called_once_with("config.yaml")
    mock_job_run.assert_awaited_once()


def test_weather_trip_scout_error_returns_exit_code_1() -> None:
    with (
        patch("app.main.Settings", side_effect=WeatherTripScoutError("boom")),
        patch("app.main.logger") as mock_logger,
    ):
        result = main(["run"])

    assert result == 1
    mock_logger.error.assert_called_once()


def test_validation_error_returns_exit_code_1() -> None:
    validation_error = ValidationError.from_exception_data("Settings", [])
    with (
        patch("app.main.Settings", side_effect=validation_error),
        patch("app.main.logger") as mock_logger,
    ):
        result = main(["run"])

    assert result == 1
    mock_logger.error.assert_called_once()


def test_unknown_command_shows_argparse_error() -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["unknown"])

    assert exc_info.value.code == 2

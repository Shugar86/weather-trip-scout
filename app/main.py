from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from typing import TYPE_CHECKING

from pydantic import ValidationError

from app.config.loader import load_config
from app.config.settings import Settings
from app.core.exceptions import WeatherTripScoutError
from app.jobs.morning_report import MorningReportJob

if TYPE_CHECKING:
    from app.config.loader import AppConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)

logger = logging.getLogger(__name__)


async def _run_job(settings: Settings, config: AppConfig, dry_run: bool) -> None:
    await MorningReportJob(settings, config).run(dry_run=dry_run)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Weather trip scout")
    subparsers = parser.add_subparsers(dest="command", required=True)

    for name in ("run", "report"):
        subparser = subparsers.add_parser(name, help="Run morning report job")
        subparser.add_argument("--config", default="config.yaml")
        subparser.add_argument(
            "--dry-run",
            action="store_true",
            help="Build the report and print it instead of sending to Telegram",
        )

    args = parser.parse_args(argv)

    try:
        # pydantic-settings reads values from the environment / .env file.
        settings = Settings()
        config = load_config(args.config)
        if args.command in {"run", "report"}:
            asyncio.run(_run_job(settings, config, args.dry_run))
    except WeatherTripScoutError as exc:
        logger.error("Error: %s", exc)
        return 1
    except ValidationError as exc:
        logger.error("Configuration validation error: %s", exc)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())

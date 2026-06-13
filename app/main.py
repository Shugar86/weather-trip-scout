import argparse
import asyncio
import logging
import sys

from app.config.loader import AppConfig, load_config  # noqa: F401
from app.config.settings import Settings
from app.jobs.morning_report import MorningReportJob

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Weather trip scout")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run morning report job")
    run_parser.add_argument("--config", default="config.yaml")

    args = parser.parse_args(argv)

    settings = Settings()  # type: ignore[call-arg]
    config = load_config(args.config)

    if args.command == "run":
        asyncio.run(MorningReportJob(settings, config).run())

    return 0


if __name__ == "__main__":
    sys.exit(main())

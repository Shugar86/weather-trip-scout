import asyncio
import logging
from datetime import date

from app.config.loader import AppConfig
from app.config.settings import Settings
from app.core.exceptions import ConfigurationError
from app.domain.models import PlaceScore, Point
from app.providers.factory import (
    build_geo_provider,
    build_map_builder,
    build_weather_provider,
)
from app.services.candidate_service import CandidateService
from app.services.forecast_service import ForecastService
from app.services.report_service import ReportService
from app.services.scoring_service import ScoringService
from app.services.telegram_service import TelegramService

logger = logging.getLogger(__name__)


class MorningReportJob:
    def __init__(self, settings: Settings, config: AppConfig) -> None:
        self.settings = settings
        self.config = config

    async def run(self, dry_run: bool = False) -> None:
        today = date.today()
        home = Point(lat=self.config.home.lat, lon=self.config.home.lon)

        geo_provider = build_geo_provider(self.config.providers.geo)
        candidate_service = CandidateService(geo_provider)
        places = await asyncio.to_thread(
            candidate_service.find_candidates,
            home,
            self.config.search.radius_km,
            self.config.search.mode,
            self.config.search.max_candidates,
        )
        logger.info("Found %d candidate places", len(places))

        primary_weather = build_weather_provider(
            self.config.providers.weather_primary, self.settings
        )
        fallback_weather = None
        if self.config.providers.weather_fallback:
            try:
                fallback_weather = build_weather_provider(
                    self.config.providers.weather_fallback, self.settings
                )
            except ConfigurationError as exc:
                # A missing fallback key must not break the free primary provider.
                logger.warning("Weather fallback unavailable, skipping: %s", exc)
        forecast_service = ForecastService(primary_weather, fallback_weather)

        scoring_service = ScoringService(
            self.config.weather_preferences,
            self.config.scoring_weights,
        )

        ranked: list[PlaceScore] = []
        for place in places:
            try:
                forecast = await asyncio.to_thread(
                    forecast_service.get_forecast, place, today
                )
                score = await asyncio.to_thread(
                    scoring_service.score_place,
                    place,
                    forecast,
                    home,
                    self.config.time.analyze_from,
                    self.config.time.analyze_to,
                )
                if score.final_score >= self.config.search.min_acceptable_score:
                    ranked.append(score)
            except Exception as exc:
                logger.warning(
                    "Failed to process place %s: %s", place.name, exc, exc_info=True
                )

        ranked.sort(key=lambda x: x.final_score, reverse=True)
        ranked = ranked[: self.config.search.top_n_places]

        map_builder = build_map_builder(self.config.providers.map, self.settings)
        report_service = ReportService(map_builder)
        report = await asyncio.to_thread(
            report_service.build_report,
            ranked,
            today,
            home,
            self.config.search.radius_km,
        )

        if dry_run:
            logger.info("Dry run: report not sent to Telegram")
            print(report.text)
            if report.image_path:
                print(f"\n[map image: {report.image_path}]")
            return

        if not self.settings.telegram_bot_token or not self.settings.telegram_chat_id:
            raise ConfigurationError(
                "TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID are required to send a report "
                "(use --dry-run to preview without sending)"
            )

        telegram = TelegramService(
            self.settings.telegram_bot_token, self.settings.telegram_chat_id
        )
        await telegram.send_report(report)
        logger.info("Morning report finished")

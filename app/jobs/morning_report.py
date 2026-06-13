import logging
from datetime import date

from app.config.loader import AppConfig
from app.config.settings import Settings
from app.domain.models import PlaceScore, Point
from app.providers.geo.overpass import OverpassProvider
from app.providers.maps.base import MapBuilder
from app.providers.maps.mapbox import MapboxBuilder
from app.providers.maps.staticmap_osm import StaticMapOSMBuilder
from app.providers.weather.open_meteo import OpenMeteoProvider
from app.providers.weather.open_weather import OpenWeatherProvider
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

    async def run(self) -> None:
        home = Point(lat=self.config.home.lat, lon=self.config.home.lon)

        geo_provider = OverpassProvider()
        candidate_service = CandidateService(geo_provider)
        places = candidate_service.find_candidates(
            home, self.config.search.radius_km, self.config.search.mode
        )
        logger.info("Found %d candidate places", len(places))

        primary_weather = OpenMeteoProvider()
        fallback_weather = (
            OpenWeatherProvider(self.settings.open_weather_api_key)
            if self.settings.open_weather_api_key
            else None
        )
        forecast_service = ForecastService(primary_weather, fallback_weather)

        scoring_service = ScoringService(
            self.config.weather_preferences,
            self.config.scoring_weights,
        )

        ranked: list[PlaceScore] = []
        for place in places:
            try:
                forecast = forecast_service.get_forecast(place, date.today())
                score = scoring_service.score_place(place, forecast, home)
                if score.final_score >= self.config.search.min_acceptable_score:
                    ranked.append(score)
            except Exception as exc:
                logger.warning("Failed to process place %s: %s", place.name, exc)

        ranked.sort(key=lambda x: x.final_score, reverse=True)
        ranked = ranked[: self.config.search.top_n_places]

        map_builder = self._build_map_builder()
        report_service = ReportService(map_builder)
        report = report_service.build_report(
            ranked, date.today(), home, self.config.search.radius_km
        )

        telegram = TelegramService(
            self.settings.telegram_bot_token, self.settings.telegram_chat_id
        )
        await telegram.send_report(report)
        logger.info("Morning report finished")

    def _build_map_builder(self) -> MapBuilder:
        if self.settings.mapbox_token:
            return MapboxBuilder(self.settings.mapbox_token)
        return StaticMapOSMBuilder()

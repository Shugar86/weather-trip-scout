import logging
from datetime import date

from app.domain.models import HourlyForecastPoint, Place
from app.providers.weather.base import WeatherProvider

logger = logging.getLogger(__name__)


class ForecastService:
    def __init__(
        self,
        primary: WeatherProvider,
        fallback: WeatherProvider | None = None,
    ) -> None:
        self.primary = primary
        self.fallback = fallback

    def get_forecast(
        self, place: Place, target_date: date
    ) -> list[HourlyForecastPoint]:
        try:
            return self.primary.get_hourly_forecast(place.point, target_date)
        except Exception as exc:
            logger.warning(
                "Primary weather provider failed for %s: %s",
                place.name,
                exc,
                exc_info=True,
            )
            if self.fallback is not None:
                return self.fallback.get_hourly_forecast(place.point, target_date)
            raise

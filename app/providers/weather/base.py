from datetime import date
from typing import Protocol, runtime_checkable

from app.domain.models import HourlyForecastPoint, Point


@runtime_checkable
class WeatherProvider(Protocol):
    def get_hourly_forecast(
        self, point: Point, target_date: date
    ) -> list[HourlyForecastPoint]: ...

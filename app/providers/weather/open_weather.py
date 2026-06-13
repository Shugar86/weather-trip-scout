import logging
from datetime import date, datetime, timezone

import requests

from app.core.exceptions import ConfigurationError, ProviderError
from app.domain.models import HourlyForecastPoint, Point

logger = logging.getLogger(__name__)


class OpenWeatherProvider:
    """Fallback weather provider; requires an API key."""

    BASE_URL = "https://api.openweathermap.org/data/3.0/onecall"

    def __init__(self, api_key: str | None) -> None:
        if not api_key:
            raise ConfigurationError(
                "OPEN_WEATHER_API_KEY is required for OpenWeatherProvider"
            )
        self.api_key = api_key

    def get_hourly_forecast(
        self, point: Point, target_date: date
    ) -> list[HourlyForecastPoint]:
        params = {
            "lat": point.lat,
            "lon": point.lon,
            "appid": self.api_key,
            "units": "metric",
            "exclude": "current,minutely,daily,alerts",
        }
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ProviderError(f"OpenWeather request failed: {exc}") from exc

        data = response.json()
        hourly = data.get("hourly", [])

        return [
            HourlyForecastPoint(
                time=datetime.fromtimestamp(h["dt"], tz=timezone.utc),
                temp_c=float(h["temp"]),
                wind_kmh=float(h["wind_speed"]) * 3.6,
                precip_mm=float(h.get("rain", {}).get("1h", 0))
                + float(h.get("snow", {}).get("1h", 0)),
                precip_probability=float(h.get("pop", 0)) * 100
                if "pop" in h
                else None,
                cloud_cover=float(h.get("clouds", 0)),
            )
            for h in hourly
            if datetime.fromtimestamp(h["dt"], tz=timezone.utc).date() == target_date
        ]

import logging
from datetime import UTC, date, datetime
from typing import Any

import requests

from app.core.exceptions import ProviderError
from app.domain.models import HourlyForecastPoint, Point

logger = logging.getLogger(__name__)


class OpenMeteoProvider:
    """Free weather provider that does not require an API key."""

    BASE_URL = "https://api.open-meteo.com/v1/forecast"

    def get_hourly_forecast(
        self, point: Point, target_date: date
    ) -> list[HourlyForecastPoint]:
        params: dict[str, Any] = {
            "latitude": point.lat,
            "longitude": point.lon,
            "hourly": [
                "temperature_2m",
                "windspeed_10m",
                "precipitation",
                "precipitation_probability",
                "cloudcover",
            ],
            "timezone": "UTC",
            "start_date": target_date.isoformat(),
            "end_date": target_date.isoformat(),
        }
        try:
            response = requests.get(self.BASE_URL, params=params, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            raise ProviderError(f"Open-Meteo request failed: {exc}") from exc

        data = response.json()
        hourly = data.get("hourly", {})
        if not isinstance(hourly, dict):
            raise ProviderError("Open-Meteo response missing valid hourly data")

        required_keys = (
            "time",
            "temperature_2m",
            "windspeed_10m",
            "precipitation",
            "precipitation_probability",
            "cloudcover",
        )
        for key in required_keys:
            if key not in hourly:
                raise ProviderError(f"Open-Meteo response missing required key: {key}")

        times = hourly["time"]
        temps = hourly["temperature_2m"]
        winds = hourly["windspeed_10m"]
        precips = hourly["precipitation"]
        probs = hourly["precipitation_probability"]
        clouds = hourly["cloudcover"]

        arrays = (times, temps, winds, precips, probs, clouds)
        length = len(times)
        if not all(len(arr) == length for arr in arrays):
            raise ProviderError("Open-Meteo hourly arrays have inconsistent lengths")

        try:
            return [
                HourlyForecastPoint(
                    time=datetime.fromisoformat(t).replace(tzinfo=UTC),
                    temp_c=float(temps[i]),
                    wind_kmh=float(winds[i]),
                    precip_mm=float(precips[i]),
                    precip_probability=(
                        float(probs[i])
                        if i < len(probs) and probs[i] is not None
                        else None
                    ),
                    cloud_cover=(
                        float(clouds[i])
                        if i < len(clouds) and clouds[i] is not None
                        else None
                    ),
                )
                for i, t in enumerate(times)
            ]
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise ProviderError(f"Open-Meteo response parsing failed: {exc}") from exc

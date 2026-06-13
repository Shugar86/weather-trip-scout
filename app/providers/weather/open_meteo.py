import logging
from datetime import date, datetime, timezone

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
        params = {
            "latitude": point.lat,
            "longitude": point.lon,
            "hourly": [
                "temperature_2m",
                "windspeed_10m",
                "precipitation",
                "precipitation_probability",
                "cloudcover",
            ],
            "timezone": "auto",
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
        times = hourly.get("time", [])
        temps = hourly.get("temperature_2m", [])
        winds = hourly.get("windspeed_10m", [])
        precips = hourly.get("precipitation", [])
        probs = hourly.get("precipitation_probability", [])
        clouds = hourly.get("cloudcover", [])

        return [
            HourlyForecastPoint(
                time=datetime.fromisoformat(t).replace(tzinfo=timezone.utc),
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

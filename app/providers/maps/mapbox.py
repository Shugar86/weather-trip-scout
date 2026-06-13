import logging
import os
import tempfile

import requests

from app.core.exceptions import ConfigurationError
from app.domain.models import PlaceScore, Point

logger = logging.getLogger(__name__)


class MapboxBuilder:
    """Optional Mapbox static map builder; requires MAPBOX_TOKEN."""

    WIDTH = 800
    HEIGHT = 600
    ZOOM = 8

    def __init__(self, token: str | None) -> None:
        if not token:
            raise ConfigurationError("MAPBOX_TOKEN is required for MapboxBuilder")
        self.token = token

    def build_map(
        self,
        ranked: list[PlaceScore],
        home: Point,
        radius_km: float,
    ) -> str | None:
        if not ranked:
            return None

        center = f"{home.lon},{home.lat}"
        url = (
            f"https://api.mapbox.com/styles/v1/mapbox/outdoors-v11/static/"
            f"{center},{self.ZOOM}/{self.WIDTH}x{self.HEIGHT}"
            f"?access_token={self.token}"
        )
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.warning("Mapbox request failed: %s", exc)
            return None

        path = os.path.join(tempfile.gettempdir(), "weather_trip_scout_mapbox.png")
        with open(path, "wb") as f:
            f.write(response.content)
        return path

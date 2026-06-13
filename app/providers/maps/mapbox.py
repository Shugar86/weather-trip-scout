import logging
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
        except requests.RequestException:
            logger.warning("Mapbox request failed", exc_info=True)
            return None

        try:
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as f:
                f.write(response.content)
            return f.name
        except OSError:
            logger.warning("Mapbox file write failed", exc_info=True)
            return None

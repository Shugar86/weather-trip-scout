import logging
import os
import tempfile

from staticmap import CircleMarker, StaticMap

from app.domain.models import PlaceScore, Point

logger = logging.getLogger(__name__)


class StaticMapOSMBuilder:
    """Builds a static map using OSM tiles; no API key required."""

    WIDTH = 800
    HEIGHT = 600
    ZOOM = 8

    def build_map(
        self,
        ranked: list[PlaceScore],
        home: Point,
        radius_km: float,
    ) -> str | None:
        if not ranked:
            return None

        m = StaticMap(self.WIDTH, self.HEIGHT)
        m.add_marker(CircleMarker((home.lon, home.lat), "red", 10))

        for place_score in ranked:
            color = self._score_color(place_score.final_score)
            p = place_score.place.point
            m.add_marker(CircleMarker((p.lon, p.lat), color, 8))

        try:
            image = m.render()
            path = os.path.join(tempfile.gettempdir(), "weather_trip_scout_map.png")
            image.save(path)
            return path
        except Exception as exc:
            logger.warning("Static map rendering failed: %s", exc)
            return None

    def _score_color(self, score: float) -> str:
        if score >= 80:
            return "green"
        if score >= 60:
            return "orange"
        return "red"

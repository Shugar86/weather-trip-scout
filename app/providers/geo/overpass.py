import requests

from app.core.exceptions import ProviderError
from app.domain.models import Place, Point


class OverpassProvider:
    """OSM-based candidate places within a radius."""

    BASE_URL = "https://overpass-api.de/api/interpreter"

    def get_candidate_places(
        self, center: Point, radius_km: float, mode: str
    ) -> list[Place]:
        if radius_km <= 0:
            raise ProviderError("radius_km must be greater than 0")

        tag = self._tag_for_mode(mode)
        query = f"""
        [out:json][timeout:25];
        (
          node[{tag}](around:{radius_km * 1000:.0f},{center.lat},{center.lon});
        );
        out body;
        """
        try:
            response = requests.post(
                self.BASE_URL,
                data={"data": query},
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            raise ProviderError(f"Overpass request failed: {exc}") from exc
        except ValueError as exc:
            raise ProviderError(f"Overpass response is not valid JSON: {exc}") from exc

        elements = data.get("elements", [])
        places = []
        for el in elements:
            lat = el.get("lat")
            lon = el.get("lon")
            if lat is None or lon is None:
                continue
            tags = el.get("tags", {})
            name = tags.get("name") or tags.get("name:en")
            if not name:
                continue
            places.append(
                Place(
                    name=name,
                    point=Point(lat=lat, lon=lon),
                    place_id=str(el.get("id")),
                    tags=tags,
                )
            )
        return places

    def _tag_for_mode(self, mode: str) -> str:
        if mode == "towns":
            return "place~'town|city|village'"
        if mode == "nature":
            return "tourism~'viewpoint|picnic_site'|natural~'peak|lake|forest'"
        return "place~'town|city|village'"

from app.domain.geo import haversine_km
from app.domain.models import Place, Point
from app.providers.geo.base import GeoProvider


class CandidateService:
    def __init__(self, provider: GeoProvider) -> None:
        self.provider = provider

    def find_candidates(
        self,
        home: Point,
        radius_km: float,
        mode: str,
        max_candidates: int | None = None,
    ) -> list[Place]:
        places = self.provider.get_candidate_places(home, radius_km, mode)
        if max_candidates is not None and len(places) > max_candidates:
            # Keep the nearest places to bound the number of weather API calls.
            places.sort(key=lambda p: haversine_km(home, p.point))
            places = places[:max_candidates]
        return places

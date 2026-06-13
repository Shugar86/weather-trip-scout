from app.domain.models import Place, Point
from app.providers.geo.base import GeoProvider


class CandidateService:
    def __init__(self, provider: GeoProvider) -> None:
        self.provider = provider

    def find_candidates(self, home: Point, radius_km: float, mode: str) -> list[Place]:
        return self.provider.get_candidate_places(home, radius_km, mode)

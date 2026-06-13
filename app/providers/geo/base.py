from typing import Protocol, runtime_checkable

from app.domain.models import Place, Point


@runtime_checkable
class GeoProvider(Protocol):
    def get_candidate_places(
        self, center: Point, radius_km: float, mode: str
    ) -> list[Place]: ...

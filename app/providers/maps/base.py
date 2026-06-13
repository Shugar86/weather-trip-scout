from typing import Protocol, runtime_checkable

from app.domain.models import PlaceScore, Point


@runtime_checkable
class MapBuilder(Protocol):
    def build_map(
        self,
        ranked: list[PlaceScore],
        home: Point,
        radius_km: float,
    ) -> str | None: ...

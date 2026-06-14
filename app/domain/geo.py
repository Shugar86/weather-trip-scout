import math

from app.domain.models import Point


def haversine_km(a: Point, b: Point) -> float:
    """Great-circle distance between two points in kilometers."""
    earth_radius_km = 6371.0
    phi1, phi2 = math.radians(a.lat), math.radians(b.lat)
    dphi = math.radians(b.lat - a.lat)
    dlambda = math.radians(b.lon - a.lon)
    x = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    return 2 * earth_radius_km * math.atan2(math.sqrt(x), math.sqrt(1 - x))

from unittest.mock import MagicMock

from app.domain.models import Place, Point
from app.providers.geo.base import GeoProvider
from app.services.candidate_service import CandidateService


def test_find_candidates_delegates_to_geo_provider() -> None:
    mock_provider = MagicMock(spec=GeoProvider)
    home = Point(lat=48.0, lon=11.0)
    expected = [Place("Test Town", Point(48.1, 11.1))]
    mock_provider.get_candidate_places.return_value = expected

    service = CandidateService(provider=mock_provider)
    result = service.find_candidates(home, radius_km=10.0, mode="towns")

    assert result == expected
    mock_provider.get_candidate_places.assert_called_once_with(home, 10.0, "towns")


def test_find_candidates_keeps_nearest_when_capped() -> None:
    mock_provider = MagicMock(spec=GeoProvider)
    home = Point(lat=48.0, lon=11.0)
    near = Place("Near", Point(48.05, 11.05))
    mid = Place("Mid", Point(48.3, 11.3))
    far = Place("Far", Point(48.8, 11.8))
    # Returned in non-distance order to prove the service sorts before truncating.
    mock_provider.get_candidate_places.return_value = [far, near, mid]

    service = CandidateService(provider=mock_provider)
    result = service.find_candidates(
        home, radius_km=200.0, mode="towns", max_candidates=2
    )

    assert result == [near, mid]


def test_find_candidates_no_cap_returns_all() -> None:
    mock_provider = MagicMock(spec=GeoProvider)
    home = Point(lat=48.0, lon=11.0)
    places = [Place("A", Point(48.1, 11.1)), Place("B", Point(48.2, 11.2))]
    mock_provider.get_candidate_places.return_value = places

    service = CandidateService(provider=mock_provider)
    result = service.find_candidates(home, radius_km=50.0, mode="towns")

    assert result == places

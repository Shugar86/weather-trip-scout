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

import pytest

from app.config.settings import Settings
from app.core.exceptions import ConfigurationError
from app.providers.factory import (
    build_geo_provider,
    build_map_builder,
    build_weather_provider,
)
from app.providers.geo.overpass import OverpassProvider
from app.providers.maps.mapbox import MapboxBuilder
from app.providers.maps.staticmap_osm import StaticMapOSMBuilder
from app.providers.weather.open_meteo import OpenMeteoProvider
from app.providers.weather.open_weather import OpenWeatherProvider


def test_build_open_meteo_provider() -> None:
    settings = Settings.model_construct(open_weather_api_key=None, mapbox_token=None)
    provider = build_weather_provider("open_meteo", settings)
    assert isinstance(provider, OpenMeteoProvider)


def test_build_open_weather_provider_requires_key() -> None:
    settings = Settings.model_construct(open_weather_api_key=None, mapbox_token=None)
    with pytest.raises(ConfigurationError):
        build_weather_provider("open_weather", settings)


def test_build_open_weather_provider_with_key() -> None:
    settings = Settings.model_construct(
        open_weather_api_key="secret", mapbox_token=None
    )
    provider = build_weather_provider("open_weather", settings)
    assert isinstance(provider, OpenWeatherProvider)
    assert provider.api_key == "secret"


def test_build_unknown_weather_provider_raises() -> None:
    settings = Settings.model_construct(open_weather_api_key=None, mapbox_token=None)
    with pytest.raises(ConfigurationError) as exc_info:
        build_weather_provider("unknown", settings)
    assert "unknown" in str(exc_info.value)


def test_build_overpass_provider() -> None:
    provider = build_geo_provider("overpass")
    assert isinstance(provider, OverpassProvider)


def test_build_unknown_geo_provider_raises() -> None:
    with pytest.raises(ConfigurationError) as exc_info:
        build_geo_provider("unknown")
    assert "unknown" in str(exc_info.value)


def test_build_staticmap_osm_builder() -> None:
    settings = Settings.model_construct(open_weather_api_key=None, mapbox_token=None)
    builder = build_map_builder("staticmap_osm", settings)
    assert isinstance(builder, StaticMapOSMBuilder)


def test_build_mapbox_builder_requires_token() -> None:
    settings = Settings.model_construct(open_weather_api_key=None, mapbox_token=None)
    with pytest.raises(ConfigurationError):
        build_map_builder("mapbox", settings)


def test_build_mapbox_builder_with_token() -> None:
    settings = Settings.model_construct(
        open_weather_api_key=None, mapbox_token="token"
    )
    builder = build_map_builder("mapbox", settings)
    assert isinstance(builder, MapboxBuilder)
    assert builder.token == "token"


def test_build_unknown_map_builder_raises() -> None:
    settings = Settings.model_construct(open_weather_api_key=None, mapbox_token=None)
    with pytest.raises(ConfigurationError) as exc_info:
        build_map_builder("unknown", settings)
    assert "unknown" in str(exc_info.value)

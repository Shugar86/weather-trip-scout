from app.config.settings import Settings
from app.core.exceptions import ConfigurationError
from app.providers.geo.base import GeoProvider
from app.providers.geo.overpass import OverpassProvider
from app.providers.maps.base import MapBuilder
from app.providers.maps.mapbox import MapboxBuilder
from app.providers.maps.staticmap_osm import StaticMapOSMBuilder
from app.providers.weather.base import WeatherProvider
from app.providers.weather.open_meteo import OpenMeteoProvider
from app.providers.weather.open_weather import OpenWeatherProvider


def build_weather_provider(name: str, settings: Settings) -> WeatherProvider:
    if name == "open_meteo":
        return OpenMeteoProvider()
    if name == "open_weather":
        if not settings.open_weather_api_key:
            raise ConfigurationError(
                "OPEN_WEATHER_API_KEY is required for open_weather provider"
            )
        return OpenWeatherProvider(settings.open_weather_api_key)
    raise ConfigurationError(f"Unknown weather provider: {name}")


def build_geo_provider(name: str) -> GeoProvider:
    if name == "overpass":
        return OverpassProvider()
    raise ConfigurationError(f"Unknown geo provider: {name}")


def build_map_builder(name: str, settings: Settings) -> MapBuilder:
    if name == "staticmap_osm":
        return StaticMapOSMBuilder()
    if name == "mapbox":
        if not settings.mapbox_token:
            raise ConfigurationError("MAPBOX_TOKEN is required for mapbox builder")
        return MapboxBuilder(settings.mapbox_token)
    raise ConfigurationError(f"Unknown map builder: {name}")

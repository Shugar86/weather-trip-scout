class WeatherTripScoutError(Exception):
    """Base exception for the project."""


class ConfigurationError(WeatherTripScoutError):
    """Missing or invalid configuration."""


class ProviderError(WeatherTripScoutError):
    """External provider request failed."""

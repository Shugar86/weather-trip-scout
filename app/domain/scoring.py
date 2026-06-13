from dataclasses import dataclass


@dataclass(frozen=True)
class WeatherPreferences:
    min_temp_c: float
    max_temp_c: float
    max_wind_kmh: float
    max_precip_mm_per_hour: float
    max_precip_probability: float
    max_cloud_cover: float
    min_good_window_hours: int


@dataclass(frozen=True)
class ScoringWeights:
    precip: float
    wind: float
    temp: float
    cloud: float
    distance: float
    good_window: float

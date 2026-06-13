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

    def __post_init__(self) -> None:
        if self.min_temp_c >= self.max_temp_c:
            raise ValueError("min_temp_c must be less than max_temp_c")
        if self.max_wind_kmh < 0:
            raise ValueError("max_wind_kmh must be non-negative")
        if self.max_precip_mm_per_hour < 0:
            raise ValueError("max_precip_mm_per_hour must be non-negative")
        if self.max_precip_probability < 0:
            raise ValueError("max_precip_probability must be non-negative")
        if self.max_cloud_cover < 0:
            raise ValueError("max_cloud_cover must be non-negative")
        if self.min_good_window_hours <= 0:
            raise ValueError("min_good_window_hours must be positive")


@dataclass(frozen=True)
class ScoringWeights:
    precip: float
    wind: float
    temp: float
    cloud: float
    distance: float
    good_window: float

    def __post_init__(self) -> None:
        for field_name, value in [
            ("precip", self.precip),
            ("wind", self.wind),
            ("temp", self.temp),
            ("cloud", self.cloud),
            ("distance", self.distance),
            ("good_window", self.good_window),
        ]:
            if value < 0:
                raise ValueError(f"{field_name} weight must be non-negative")

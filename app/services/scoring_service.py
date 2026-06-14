import logging
from datetime import date, datetime, time, timedelta

from app.domain.geo import haversine_km
from app.domain.models import HourlyForecastPoint, Place, PlaceScore, Point
from app.domain.scoring import ScoringWeights, WeatherPreferences

logger = logging.getLogger(__name__)


class ScoringService:
    def __init__(self, prefs: WeatherPreferences, weights: ScoringWeights) -> None:
        self.prefs = prefs
        self.weights = weights

    def score_place(
        self,
        place: Place,
        forecast: list[HourlyForecastPoint],
        home: Point,
        analyze_from: time,
        analyze_to: time,
    ) -> PlaceScore:
        forecast = self._filter_window(forecast, analyze_from, analyze_to)
        if not forecast:
            return self._zero_score(
                place, summary="No forecast data for analysis window"
            )

        hourly_scores = [self._hour_score(h) for h in forecast]
        avg_score = sum(hourly_scores) / len(hourly_scores)

        window_start, window_end = self._best_good_window(forecast)
        window_hours = (
            (
                datetime.combine(date.min, window_end)
                - datetime.combine(date.min, window_start)
            ).seconds
            / 3600
            if window_start and window_end
            else 0
        )

        distance_km = haversine_km(home, place.point)
        distance_score = max(0.0, 100.0 - distance_km)

        good_window_score = min(
            100.0, window_hours / self.prefs.min_good_window_hours * 100
        )

        breakdown = {
            "weather_avg": avg_score,
            "distance": distance_score,
            "good_window": good_window_score,
        }

        final = (
            avg_score
            * (
                self.weights.precip
                + self.weights.wind
                + self.weights.temp
                + self.weights.cloud
            )
            / 100
            + distance_score * self.weights.distance / 100
            + good_window_score * self.weights.good_window / 100
        )

        summary = self._summary(final, window_start, window_end)

        return PlaceScore(
            place=place,
            final_score=min(100.0, max(0.0, final)),
            best_time_start=window_start or time(0, 0),
            best_time_end=window_end or time(0, 0),
            summary=summary,
            breakdown=breakdown,
        )

    def _hour_score(self, hour: HourlyForecastPoint) -> float:
        score = 100.0
        if hour.precip_mm > self.prefs.max_precip_mm_per_hour:
            score -= 40 * (hour.precip_mm / max(self.prefs.max_precip_mm_per_hour, 0.1))
        if (
            hour.precip_probability is not None
            and hour.precip_probability > self.prefs.max_precip_probability
        ):
            score -= 20 * (
                (hour.precip_probability - self.prefs.max_precip_probability) / 100
            )
        if hour.wind_kmh > self.prefs.max_wind_kmh:
            score -= 20 * (
                (hour.wind_kmh - self.prefs.max_wind_kmh)
                / max(self.prefs.max_wind_kmh, 1)
            )
        if hour.temp_c < self.prefs.min_temp_c or hour.temp_c > self.prefs.max_temp_c:
            score -= 15
        if (
            hour.cloud_cover is not None
            and hour.cloud_cover > self.prefs.max_cloud_cover
        ):
            score -= 10 * ((hour.cloud_cover - self.prefs.max_cloud_cover) / 100)
        return max(0.0, score)

    def _best_good_window(
        self, forecast: list[HourlyForecastPoint]
    ) -> tuple[time | None, time | None]:
        good = [self._is_good_hour(h) for h in forecast]
        best_start: time | None = None
        best_end: time | None = None
        current_start: time | None = None
        for i, ok in enumerate(good):
            if ok and current_start is None:
                current_start = forecast[i].time.time()
            if (not ok or i == len(good) - 1) and current_start is not None:
                end = forecast[i].time.time() if ok else forecast[i - 1].time.time()
                current_hours = self._window_duration_hours(current_start, end)
                best_hours = (
                    self._window_duration_hours(best_start, best_end)
                    if best_start is not None and best_end is not None
                    else 0.0
                )
                if best_start is None or current_hours > best_hours:
                    best_start, best_end = current_start, end
                current_start = None
        return best_start, best_end

    def _window_duration_hours(self, start: time, end: time) -> float:
        start_dt = datetime.combine(date.min, start)
        end_dt = datetime.combine(date.min, end)
        if end_dt < start_dt:
            end_dt += timedelta(days=1)
        return (end_dt - start_dt).seconds / 3600

    def _is_good_hour(self, hour: HourlyForecastPoint) -> bool:
        return (
            hour.precip_mm <= self.prefs.max_precip_mm_per_hour
            and (
                hour.precip_probability is None
                or hour.precip_probability <= self.prefs.max_precip_probability
            )
            and hour.wind_kmh <= self.prefs.max_wind_kmh
            and self.prefs.min_temp_c <= hour.temp_c <= self.prefs.max_temp_c
            and (
                hour.cloud_cover is None
                or hour.cloud_cover <= self.prefs.max_cloud_cover
            )
        )

    def _filter_window(
        self,
        forecast: list[HourlyForecastPoint],
        analyze_from: time,
        analyze_to: time,
    ) -> list[HourlyForecastPoint]:
        def _in_window(hour: HourlyForecastPoint) -> bool:
            t = hour.time.time()
            if analyze_from <= analyze_to:
                return analyze_from <= t <= analyze_to
            return t >= analyze_from or t <= analyze_to

        return [h for h in forecast if _in_window(h)]

    def _zero_score(
        self, place: Place, summary: str = "No forecast data"
    ) -> PlaceScore:
        return PlaceScore(
            place=place,
            final_score=0.0,
            best_time_start=time(0, 0),
            best_time_end=time(0, 0),
            summary=summary,
            breakdown={},
        )

    def _summary(self, score: float, start: time | None, end: time | None) -> str:
        if start is not None and end is not None:
            window = f", best window {start}-{end}"
        else:
            window = ""
        if score >= 80:
            return f"Excellent conditions{window}"
        if score >= 60:
            return f"Good conditions{window}"
        if score >= 40:
            return "Acceptable but with caveats"
        return "Poor conditions"

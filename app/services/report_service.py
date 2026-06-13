from datetime import date

from app.domain.models import PlaceScore, Point, ReportPayload
from app.providers.maps.base import MapBuilder


class ReportService:
    def __init__(self, map_builder: MapBuilder) -> None:
        self.map_builder = map_builder

    def build_report(
        self,
        ranked: list[PlaceScore],
        report_date: date,
        home: Point,
        radius_km: float,
    ) -> ReportPayload:
        text = self.build_text(ranked, report_date)
        image_path = self.map_builder.build_map(ranked, home, radius_km)
        return ReportPayload(text=text, image_path=image_path)

    def build_text(self, ranked: list[PlaceScore], report_date: date) -> str:
        header = f"🌤 Weather trip scout for {report_date.isoformat()}\n\n"
        if not ranked:
            return header + "No good destinations today. Try again tomorrow!"

        lines = [header, f"Top {len(ranked)} destinations within radius:\n"]
        for i, ps in enumerate(ranked, start=1):
            lines.append(
                f"{i}. {ps.place.name} — score {ps.final_score:.0f}\n"
                f"   Best window: {ps.best_time_start}–{ps.best_time_end}\n"
                f"   {ps.summary}"
            )
        return "\n".join(lines)

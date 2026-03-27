from datetime import date
from uuid import UUID

from pydantic import BaseModel


class LabelerClassCountSchema(BaseModel):
    labeler_id: UUID
    username: str
    counts: dict[str, int]


class DailyCountSchema(BaseModel):
    date: date
    counts: dict[str, int]


class LabelerDailyActivitySchema(BaseModel):
    labeler_id: UUID
    username: str
    daily: list[DailyCountSchema]


class DailyLabelerTotalSchema(BaseModel):
    labeler_id: UUID
    username: str
    count: int


class DailyTotalSchema(BaseModel):
    date: date
    labelers: list[DailyLabelerTotalSchema]


class ProjectStatsResponse(BaseModel):
    total_images: int
    labeled_images: int
    class_distribution: dict[str, int]
    labeler_class_counts: list[LabelerClassCountSchema]
    labeler_daily_activity: list[LabelerDailyActivitySchema]
    daily_totals: list[DailyTotalSchema]

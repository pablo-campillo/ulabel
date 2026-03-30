"""Pydantic schemas for project statistics responses."""

from datetime import date
from uuid import UUID

from pydantic import BaseModel


class LabelerClassCountSchema(BaseModel):
    """Per-labeler label class counts within a project."""
    labeler_id: UUID
    username: str
    counts: dict[str, int]


class DailyCountSchema(BaseModel):
    """Label counts by class for a single day."""

    date: date
    counts: dict[str, int]


class LabelerDailyActivitySchema(BaseModel):
    """Daily labelling activity breakdown for a single labeler."""
    labeler_id: UUID
    username: str
    daily: list[DailyCountSchema]


class DailyLabelerTotalSchema(BaseModel):
    """Total label count for a single labeler on a single day."""

    labeler_id: UUID
    username: str
    count: int


class DailyTotalSchema(BaseModel):
    """Aggregate daily totals with per-labeler breakdowns."""
    date: date
    labelers: list[DailyLabelerTotalSchema]


class ProjectStatsResponse(BaseModel):
    """Complete labelling statistics for a project."""

    total_images: int
    labeled_images: int
    class_distribution: dict[str, int]
    labeler_class_counts: list[LabelerClassCountSchema]
    labeler_daily_activity: list[LabelerDailyActivitySchema]
    daily_totals: list[DailyTotalSchema]

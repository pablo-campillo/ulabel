"""create import_jobs table

Revision ID: 0004_create_import_jobs_table
Revises: 0003_unique_project_name
Create Date: 2026-04-04
"""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import UUID

revision = "0004_create_import_jobs_table"
down_revision = "0003_unique_project_name"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "import_jobs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("project_id", UUID(as_uuid=True), sa.ForeignKey("projects.id"), nullable=False, index=True),
        sa.Column("prefix", sa.String(1024), nullable=False),
        sa.Column("status", sa.String(50), nullable=False, index=True),
        sa.Column("imported", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error", sa.Text, nullable=True),
    )


def downgrade() -> None:
    op.drop_table("import_jobs")

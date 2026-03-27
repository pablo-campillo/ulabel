"""add created_at to projects

Revision ID: 0002_add_project_created_at
Revises: 0001_add_label_created_at
Create Date: 2026-03-27
"""

from alembic import op
import sqlalchemy as sa

revision = "0002_add_project_created_at"
down_revision = "0001_add_label_created_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "projects",
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )


def downgrade() -> None:
    op.drop_column("projects", "created_at")

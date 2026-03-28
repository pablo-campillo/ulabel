"""add unique constraint to project name

Revision ID: 0003_unique_project_name
Revises: 0002_add_project_created_at
Create Date: 2026-03-28
"""

from alembic import op

revision = "0003_unique_project_name"
down_revision = "0002_add_project_created_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_unique_constraint("uq_projects_name", "projects", ["name"])


def downgrade() -> None:
    op.drop_constraint("uq_projects_name", "projects", type_="unique")

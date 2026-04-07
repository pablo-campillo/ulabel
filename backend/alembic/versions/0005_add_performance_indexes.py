"""add composite indexes for query optimization

Revision ID: 0005_add_performance_indexes
Revises: 0004_create_import_jobs_table
Create Date: 2026-04-05
"""

from alembic import op

revision = "0005_add_performance_indexes"
down_revision = "0004_create_import_jobs_table"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index("ix_images_project_status", "images", ["project_id", "status"])
    op.create_index("ix_images_status_assigned_at", "images", ["status", "assigned_at"])
    op.create_index("ix_project_labelers_labeler_id", "project_labelers", ["labeler_id"])
    op.create_index("ix_label_records_project_image", "label_records", ["project_id", "image_id"])
    op.create_index(
        "ix_label_records_project_labeler", "label_records", ["project_id", "labeler_id"]
    )
    op.create_index(
        "ix_projects_created_at",
        "projects",
        ["created_at"],
        postgresql_ops={"created_at": "DESC"},
    )


def downgrade() -> None:
    op.drop_index("ix_projects_created_at", table_name="projects")
    op.drop_index("ix_label_records_project_labeler", table_name="label_records")
    op.drop_index("ix_label_records_project_image", table_name="label_records")
    op.drop_index("ix_project_labelers_labeler_id", table_name="project_labelers")
    op.drop_index("ix_images_status_assigned_at", table_name="images")
    op.drop_index("ix_images_project_status", table_name="images")

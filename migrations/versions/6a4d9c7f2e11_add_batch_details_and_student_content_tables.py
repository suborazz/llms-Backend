"""add batch details and student content tables

Revision ID: 6a4d9c7f2e11
Revises: ad47f05fbe3d
Create Date: 2026-04-23 14:10:00.000000
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "6a4d9c7f2e11"
down_revision = "ad47f05fbe3d"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "batch_details",
        sa.Column("batch_id", sa.String(length=36), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("room_name", sa.String(length=255), nullable=True),
        sa.Column("schedule_notes", sa.Text(), nullable=True),
        sa.Column("start_date", sa.String(length=40), nullable=True),
        sa.Column("end_date", sa.String(length=40), nullable=True),
        sa.ForeignKeyConstraint(["batch_id"], ["batches.batch_id"]),
        sa.PrimaryKeyConstraint("batch_id"),
    )

    op.create_table(
        "content_profiles",
        sa.Column("content_id", sa.String(length=36), nullable=False),
        sa.Column("category", sa.String(length=40), nullable=False),
        sa.Column("body_text", sa.Text(), nullable=True),
        sa.Column("instructions", sa.Text(), nullable=True),
        sa.Column("downloadable", sa.Boolean(), nullable=False),
        sa.Column("response_type", sa.String(length=40), nullable=True),
        sa.ForeignKeyConstraint(["content_id"], ["contents.content_id"]),
        sa.PrimaryKeyConstraint("content_id"),
    )

    op.create_table(
        "student_submissions",
        sa.Column("submission_id", sa.String(length=36), nullable=False),
        sa.Column("institute_id", sa.String(length=36), nullable=False),
        sa.Column("content_id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("response_type", sa.String(length=40), nullable=False),
        sa.Column("response_text", sa.Text(), nullable=True),
        sa.Column("response_url", sa.Text(), nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["content_id"], ["contents.content_id"]),
        sa.ForeignKeyConstraint(["institute_id"], ["institutes.institute_id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.user_id"]),
        sa.PrimaryKeyConstraint("submission_id"),
    )
    op.create_index(
        op.f("ix_student_submissions_institute_id"),
        "student_submissions",
        ["institute_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_student_submissions_institute_id"), table_name="student_submissions")
    op.drop_table("student_submissions")
    op.drop_table("content_profiles")
    op.drop_table("batch_details")

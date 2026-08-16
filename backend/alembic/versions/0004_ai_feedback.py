"""AI analysis sessions and training feedback.

Revision ID: 0004_ai_feedback
Revises: 0003_refresh_tokens
Create Date: 2026-08-16
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0004_ai_feedback"
down_revision: Union[str, None] = "0003_refresh_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "allow_training_data_collection",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )
    op.create_table(
        "ai_analyses",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("analysis_type", sa.String(length=20), nullable=False),
        sa.Column("image_reference", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_ai_analyses_user_id", "ai_analyses", ["user_id"])
    op.create_index("ix_ai_analyses_image_reference", "ai_analyses", ["image_reference"])
    op.create_table(
        "ai_analysis_feedback",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("analysis_id", sa.String(length=36), nullable=True),
        sa.Column("image_reference", sa.String(length=80), nullable=True),
        sa.Column("predicted_food", sa.String(length=255), nullable=False),
        sa.Column("corrected_food", sa.String(length=255), nullable=False),
        sa.Column("predicted_quantity", sa.Numeric(10, 2), nullable=False),
        sa.Column("corrected_quantity", sa.Numeric(10, 2), nullable=False),
        sa.Column("predicted_unit", sa.String(length=40), nullable=False),
        sa.Column("corrected_unit", sa.String(length=40), nullable=False),
        sa.Column("predicted_confidence", sa.Numeric(4, 3), nullable=True),
        sa.Column("confirmed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("include_in_training", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["analysis_id"], ["ai_analyses.id"], ondelete="SET NULL"),
    )
    op.create_index("ix_ai_analysis_feedback_user_id", "ai_analysis_feedback", ["user_id"])
    op.create_index("ix_ai_analysis_feedback_analysis_id", "ai_analysis_feedback", ["analysis_id"])
    op.create_index("ix_ai_analysis_feedback_training", "ai_analysis_feedback", ["include_in_training"])


def downgrade() -> None:
    op.drop_index("ix_ai_analysis_feedback_training", table_name="ai_analysis_feedback")
    op.drop_index("ix_ai_analysis_feedback_analysis_id", table_name="ai_analysis_feedback")
    op.drop_index("ix_ai_analysis_feedback_user_id", table_name="ai_analysis_feedback")
    op.drop_table("ai_analysis_feedback")
    op.drop_index("ix_ai_analyses_image_reference", table_name="ai_analyses")
    op.drop_index("ix_ai_analyses_user_id", table_name="ai_analyses")
    op.drop_table("ai_analyses")
    op.drop_column("users", "allow_training_data_collection")

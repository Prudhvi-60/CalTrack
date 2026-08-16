"""Add ai_corrections for user edits of AI portion/name predictions.

Revision ID: 0002_ai_corrections
Revises: 0001_initial
Create Date: 2026-08-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_ai_corrections"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "ai_corrections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("food", sa.String(length=255), nullable=False),
        sa.Column("predicted_name", sa.String(length=255), nullable=False),
        sa.Column("predicted_quantity", sa.Numeric(10, 2), nullable=False),
        sa.Column("predicted_unit", sa.String(length=40), nullable=False),
        sa.Column("corrected_name", sa.String(length=255), nullable=False),
        sa.Column("corrected_quantity", sa.Numeric(10, 2), nullable=False),
        sa.Column("corrected_unit", sa.String(length=40), nullable=False),
        sa.Column("analysis_type", sa.String(length=20), nullable=False, server_default="food"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_ai_corrections_user_id", "ai_corrections", ["user_id"])
    op.create_index("ix_ai_corrections_food", "ai_corrections", ["food"])


def downgrade() -> None:
    op.drop_index("ix_ai_corrections_food", table_name="ai_corrections")
    op.drop_index("ix_ai_corrections_user_id", table_name="ai_corrections")
    op.drop_table("ai_corrections")

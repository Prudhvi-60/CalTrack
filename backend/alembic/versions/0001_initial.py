"""Initial schema: users, goals, meals, food_entries, micronutrients.

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

meal_type = sa.Enum("BREAKFAST", "LUNCH", "DINNER", "SNACK", name="meal_type")


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "goals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("daily_calorie_target", sa.Numeric(8, 2), nullable=False),
        sa.Column("protein_target", sa.Numeric(8, 2), nullable=False),
        sa.Column("carb_target", sa.Numeric(8, 2), nullable=False),
        sa.Column("fat_target", sa.Numeric(8, 2), nullable=False),
        sa.Column("weight_goal", sa.Numeric(6, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.UniqueConstraint("user_id", name="uq_goals_user_id"),
        sa.CheckConstraint("daily_calorie_target >= 0", name="ck_goals_calories_non_negative"),
        sa.CheckConstraint("protein_target >= 0", name="ck_goals_protein_non_negative"),
        sa.CheckConstraint("carb_target >= 0", name="ck_goals_carb_non_negative"),
        sa.CheckConstraint("fat_target >= 0", name="ck_goals_fat_non_negative"),
    )
    op.create_index("ix_goals_user_id", "goals", ["user_id"])

    op.create_table(
        "meals",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("meal_type", meal_type, nullable=False),
        sa.Column("consumed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_meals_user_id", "meals", ["user_id"])
    op.create_index("ix_meals_consumed_at", "meals", ["consumed_at"])
    op.create_index("ix_meals_user_id_consumed_at", "meals", ["user_id", "consumed_at"])
    op.create_index("ix_meals_user_id_meal_type", "meals", ["user_id", "meal_type"])

    op.create_table(
        "food_entries",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("meal_id", sa.Integer(), nullable=False),
        sa.Column("food_name", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Numeric(10, 2), nullable=False),
        sa.Column("unit", sa.String(length=40), nullable=False),
        sa.Column("calories", sa.Numeric(10, 2), nullable=False),
        sa.Column("protein", sa.Numeric(10, 2), nullable=False),
        sa.Column("carbohydrates", sa.Numeric(10, 2), nullable=False),
        sa.Column("fat", sa.Numeric(10, 2), nullable=False),
        sa.Column("fiber", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("sugar", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["meal_id"], ["meals.id"], ondelete="CASCADE"),
        sa.CheckConstraint("quantity >= 0", name="ck_food_entries_quantity_non_negative"),
        sa.CheckConstraint("calories >= 0", name="ck_food_entries_calories_non_negative"),
        sa.CheckConstraint("protein >= 0", name="ck_food_entries_protein_non_negative"),
        sa.CheckConstraint("carbohydrates >= 0", name="ck_food_entries_carbohydrates_non_negative"),
        sa.CheckConstraint("fat >= 0", name="ck_food_entries_fat_non_negative"),
        sa.CheckConstraint("fiber >= 0", name="ck_food_entries_fiber_non_negative"),
        sa.CheckConstraint("sugar >= 0", name="ck_food_entries_sugar_non_negative"),
    )
    op.create_index("ix_food_entries_meal_id", "food_entries", ["meal_id"])

    op.create_table(
        "micronutrients",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("food_entry_id", sa.Integer(), nullable=False),
        sa.Column("nutrient_name", sa.String(length=80), nullable=False),
        sa.Column("amount", sa.Numeric(12, 4), nullable=False),
        sa.Column("unit", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["food_entry_id"], ["food_entries.id"], ondelete="CASCADE"),
        sa.CheckConstraint("amount >= 0", name="ck_micronutrients_amount_non_negative"),
    )
    op.create_index("ix_micronutrients_food_entry_id", "micronutrients", ["food_entry_id"])
    op.create_index("ix_micronutrients_nutrient_name", "micronutrients", ["nutrient_name"])


def downgrade() -> None:
    op.drop_index("ix_micronutrients_nutrient_name", table_name="micronutrients")
    op.drop_index("ix_micronutrients_food_entry_id", table_name="micronutrients")
    op.drop_table("micronutrients")
    op.drop_index("ix_food_entries_meal_id", table_name="food_entries")
    op.drop_table("food_entries")
    op.drop_index("ix_meals_user_id_meal_type", table_name="meals")
    op.drop_index("ix_meals_user_id_consumed_at", table_name="meals")
    op.drop_index("ix_meals_consumed_at", table_name="meals")
    op.drop_index("ix_meals_user_id", table_name="meals")
    op.drop_table("meals")
    meal_type.drop(op.get_bind(), checkfirst=True)
    op.drop_index("ix_goals_user_id", table_name="goals")
    op.drop_table("goals")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

from datetime import date as Date

from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import MealType
from app.schemas.meal import MealPublic


class PdfPreviewRow(BaseModel):
    index: int
    valid: bool
    errors: list[str] = Field(default_factory=list)
    date: Date | None = None
    meal_type: MealType | None = None
    food_name: str | None = None
    quantity: Decimal | None = None
    unit: str | None = None
    calories: Decimal | None = None
    protein: Decimal | None = None
    carbohydrates: Decimal | None = None
    fat: Decimal | None = None
    fiber: Decimal | None = None
    sugar: Decimal | None = None


class PdfPreviewResponse(BaseModel):
    rows: list[PdfPreviewRow]
    valid_count: int
    invalid_count: int
    warnings: list[str] = Field(default_factory=list)


class PdfImportRow(BaseModel):
    date: Date
    meal_type: MealType
    food_name: str = Field(min_length=1, max_length=255)
    quantity: Decimal = Field(ge=0)
    unit: str = Field(min_length=1, max_length=40)
    calories: Decimal = Field(ge=0)
    protein: Decimal = Field(ge=0)
    carbohydrates: Decimal = Field(ge=0)
    fat: Decimal = Field(ge=0)
    fiber: Decimal = Field(default=Decimal("0"), ge=0)
    sugar: Decimal = Field(default=Decimal("0"), ge=0)


class PdfConfirmRequest(BaseModel):
    rows: list[PdfImportRow] = Field(min_length=1, max_length=200)


class PdfConfirmResponse(BaseModel):
    imported_meals: int
    imported_foods: int
    meals: list[MealPublic]

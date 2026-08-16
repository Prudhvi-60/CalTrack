from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator

from app.models.enums import MealType, NutrientName

ConfidenceLevel = Literal["HIGH", "MEDIUM", "LOW"]
NutritionSource = Literal["llm", "label", "database", "unmatched"]


class DecimalJsonModel(BaseModel):
    @field_serializer("*", when_used="json")
    def serialize_decimals(self, value: object) -> object:
        return float(value) if isinstance(value, Decimal) else value


class AnalyzedMicronutrient(DecimalJsonModel):
    nutrient_name: NutrientName
    amount: Decimal = Field(ge=0, le=100000)
    unit: str = Field(min_length=1, max_length=20)


class VisionDetectedFood(BaseModel):
    model_config = ConfigDict(extra="ignore")

    name: str = Field(min_length=1, max_length=255)
    quantity: Decimal = Field(gt=0, le=30)
    unit: str = Field(min_length=1, max_length=40)
    confidence: float = Field(default=0.5, ge=0, le=1)


class VisionFoodPhotoResult(BaseModel):
    model_config = ConfigDict(extra="ignore")

    food_items: list[VisionDetectedFood] = Field(min_length=1)
    meal_type: str | None = None
    notes: str = ""
    confidence: float | None = Field(default=None, ge=0, le=1)


class AnalyzedFoodItem(DecimalJsonModel):
    name: str = Field(min_length=1, max_length=255)
    quantity: Decimal = Field(gt=0, le=50)
    unit: str = Field(min_length=1, max_length=40)
    calories: Decimal = Field(ge=0, le=2500)
    protein: Decimal = Field(ge=0, le=400)
    carbohydrates: Decimal = Field(ge=0, le=400)
    fat: Decimal = Field(ge=0, le=400)
    fiber: Decimal = Field(default=Decimal("0"), ge=0, le=200)
    sugar: Decimal = Field(default=Decimal("0"), ge=0, le=200)
    micronutrients: list[AnalyzedMicronutrient] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)
    confidence_level: ConfidenceLevel = "MEDIUM"
    estimated_weight_g: Decimal | None = Field(default=None, ge=0, le=2000)
    nutrition_source: NutritionSource = "llm"
    matched_food: str | None = None


class FoodAnalysisResult(DecimalJsonModel):
    analysis_type: str
    food_items: list[AnalyzedFoodItem] = Field(min_length=1)
    confidence: float = Field(ge=0, le=1)
    notes: str = ""
    meal_type: MealType | None = None
    serving_size: str | None = None
    servings_per_container: float | None = Field(default=None, ge=0)
    warnings: list[str] = Field(default_factory=list)
    analysis_id: str | None = None

    @field_validator("analysis_type")
    @classmethod
    def valid_type(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in {"food", "label"}:
            raise ValueError("analysis_type must be food or label")
        return normalized


class AiCorrectionItem(BaseModel):
    predicted_name: str = Field(min_length=1, max_length=255)
    predicted_quantity: Decimal = Field(ge=0, le=50)
    predicted_unit: str = Field(min_length=1, max_length=40)
    corrected_name: str = Field(min_length=1, max_length=255)
    corrected_quantity: Decimal = Field(ge=0, le=50)
    corrected_unit: str = Field(min_length=1, max_length=40)
    predicted_confidence: float | None = Field(default=None, ge=0, le=1)
    confirmed: bool | None = None


class AiCorrectionCreate(BaseModel):
    analysis_type: str = Field(default="food")
    analysis_id: str | None = None
    items: list[AiCorrectionItem] = Field(min_length=1, max_length=40)

    @field_validator("analysis_type")
    @classmethod
    def valid_analysis_type(cls, value: str) -> str:
        normalized = value.lower().strip()
        if normalized not in {"food", "label"}:
            raise ValueError("analysis_type must be food or label")
        return normalized


class AiCorrectionPublic(DecimalJsonModel):
    id: int
    food: str
    predicted_quantity: Decimal
    predicted_unit: str
    corrected_quantity: Decimal
    corrected_unit: str
    predicted_name: str
    corrected_name: str
    confirmed: bool = False
    include_in_training: bool = False
    analysis_id: str | None = None

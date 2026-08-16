export type AnalysisType = "food" | "label";
export type ConfidenceLevel = "HIGH" | "MEDIUM" | "LOW";
export type NutritionSource = "llm" | "database" | "label" | "unmatched";

export type AnalyzedMicronutrient = {
  nutrient_name: string;
  amount: number;
  unit: string;
};

export type AnalyzedFoodItem = {
  name: string;
  quantity: number;
  unit: string;
  calories: number;
  protein: number;
  carbohydrates: number;
  fat: number;
  fiber: number;
  sugar: number;
  micronutrients: AnalyzedMicronutrient[];
  confidence?: number;
  confidence_level?: ConfidenceLevel;
  estimated_weight_g?: number | null;
  nutrition_source?: NutritionSource;
  matched_food?: string | null;
};

export type FoodAnalysis = {
  analysis_type: AnalysisType;
  food_items: AnalyzedFoodItem[];
  confidence: number;
  notes: string;
  meal_type?: "BREAKFAST" | "LUNCH" | "DINNER" | "SNACK" | null;
  serving_size?: string | null;
  servings_per_container?: number | null;
  warnings: string[];
  analysis_id?: string | null;
};

export type AiCorrectionItem = {
  predicted_name: string;
  predicted_quantity: number;
  predicted_unit: string;
  corrected_name: string;
  corrected_quantity: number;
  corrected_unit: string;
  predicted_confidence?: number | null;
  confirmed?: boolean;
};

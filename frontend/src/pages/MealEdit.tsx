import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { emptyFoodEntry } from "@/components/meals/emptyFoodEntry";
import { MealForm } from "@/components/meals/MealForm";
import { useMeal, useReplaceMeal } from "@/hooks/useMeals";
import { getApiErrorMessage } from "@/api/auth";
import { toDateTimeLocal } from "@/utils/datetime";
import type { MealFormValues } from "@/schemas/meal";
import type { MealPayload } from "@/types/meal";
import { NUTRIENT_NAMES } from "@/types/meal";
import { PageHeader } from "@/components/ui/page-header";
import { ErrorAlert } from "@/components/ui/error-alert";
import { PageSkeleton } from "@/components/ui/skeleton";
import { usePageTitle } from "@/hooks/usePageTitle";

export function MealEdit() {
  usePageTitle("Edit meal");
  const { mealId } = useParams();
  const id = Number(mealId);
  const navigate = useNavigate();
  const mealQuery = useMeal(id);
  const replaceMeal = useReplaceMeal(id);
  const [serverError, setServerError] = useState<string | null>(null);

  async function onSubmit(payload: MealPayload) {
    setServerError(null);
    try {
      await replaceMeal.mutateAsync(payload);
      navigate(`/meals/${id}`);
    } catch (error) {
      setServerError(getApiErrorMessage(error, "Could not update meal"));
    }
  }

  if (mealQuery.isLoading) {
    return <PageSkeleton cards={2} />;
  }
  if (mealQuery.isError || !mealQuery.data) {
    return (
      <ErrorAlert
        message={getApiErrorMessage(mealQuery.error, "Meal not found")}
        onRetry={() => void mealQuery.refetch()}
      />
    );
  }

  const meal = mealQuery.data;
  const defaultValues: MealFormValues = {
    meal_type: meal.meal_type,
    consumed_at: toDateTimeLocal(meal.consumed_at),
    notes: meal.notes ?? "",
    food_entries:
      meal.food_entries.length > 0
        ? meal.food_entries.map((entry) => ({
            food_name: entry.food_name,
            quantity: entry.quantity,
            unit: entry.unit,
            calories: entry.calories,
            protein: entry.protein,
            carbohydrates: entry.carbohydrates,
            fat: entry.fat,
            fiber: entry.fiber,
            sugar: entry.sugar,
            micronutrients: entry.micronutrients.map((micro) => ({
              nutrient_name: (NUTRIENT_NAMES as readonly string[]).includes(micro.nutrient_name)
                ? (micro.nutrient_name as (typeof NUTRIENT_NAMES)[number])
                : "Vitamin C",
              amount: micro.amount,
              unit: micro.unit,
            })),
          }))
        : [emptyFoodEntry],
  };

  return (
    <section className="space-y-6">
      <PageHeader title="Edit meal" description="Saving replaces this meal and all of its food entries." />
      <MealForm
        defaultValues={defaultValues}
        submitLabel="Save changes"
        onSubmit={onSubmit}
        serverError={serverError}
        isSubmitting={replaceMeal.isPending}
      />
      <Link className="text-sm text-primary underline underline-offset-4" to={`/meals/${id}`}>
        Cancel
      </Link>
    </section>
  );
}

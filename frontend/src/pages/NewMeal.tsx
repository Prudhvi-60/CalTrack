import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { emptyFoodEntry } from "@/components/meals/emptyFoodEntry";
import { MealForm } from "@/components/meals/MealForm";
import { useCreateMeal } from "@/hooks/useMeals";
import { getApiErrorMessage } from "@/api/auth";
import { toDateTimeLocal } from "@/utils/datetime";
import type { MealPayload } from "@/types/meal";
import { PageHeader } from "@/components/ui/page-header";
import { usePageTitle } from "@/hooks/usePageTitle";

export function NewMeal() {
  usePageTitle("New meal");
  const navigate = useNavigate();
  const createMeal = useCreateMeal();
  const [serverError, setServerError] = useState<string | null>(null);

  async function onSubmit(payload: MealPayload) {
    setServerError(null);
    try {
      const meal = await createMeal.mutateAsync(payload);
      navigate(`/meals/${meal.id}`);
    } catch (error) {
      setServerError(getApiErrorMessage(error, "Could not save meal"));
    }
  }

  return (
    <section className="space-y-6">
      <PageHeader
        title="New meal"
        description="Add one or more foods. Nutrition values cannot be negative."
      />
      <MealForm
        defaultValues={{
          meal_type: "BREAKFAST",
          consumed_at: toDateTimeLocal(new Date().toISOString()),
          notes: "",
          food_entries: [emptyFoodEntry],
        }}
        submitLabel="Save meal"
        onSubmit={onSubmit}
        serverError={serverError}
        isSubmitting={createMeal.isPending}
      />
      <Link className="text-sm text-primary underline underline-offset-4" to="/meals">
        Back to meals
      </Link>
    </section>
  );
}

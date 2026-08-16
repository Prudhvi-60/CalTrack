import { useState } from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useDeleteMeal, useMeal } from "@/hooks/useMeals";
import { getApiErrorMessage } from "@/api/auth";
import { MEAL_TYPE_LABELS, formatGrams } from "@/utils/meals";
import { formatDateTime } from "@/utils/datetime";
import { PageHeader } from "@/components/ui/page-header";
import { ErrorAlert } from "@/components/ui/error-alert";
import { PageSkeleton } from "@/components/ui/skeleton";
import { usePageTitle } from "@/hooks/usePageTitle";

export function MealDetails() {
  usePageTitle("Meal");
  const { mealId } = useParams();
  const id = Number(mealId);
  const navigate = useNavigate();
  const mealQuery = useMeal(id);
  const removeMeal = useDeleteMeal();
  const [confirmDelete, setConfirmDelete] = useState(false);

  async function onDelete() {
    await removeMeal.mutateAsync(id);
    navigate("/meals");
  }

  if (mealQuery.isLoading) {
    return <PageSkeleton cards={3} />;
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

  return (
    <section className="space-y-6">
      <PageHeader
        title={MEAL_TYPE_LABELS[meal.meal_type]}
        description={formatDateTime(meal.consumed_at)}
        actions={
          <div className="flex flex-wrap gap-2">
            <Button asChild variant="secondary">
              <Link to={`/meals/${meal.id}/edit`}>Edit</Link>
            </Button>
            {!confirmDelete ? (
              <Button type="button" variant="outline" onClick={() => setConfirmDelete(true)}>
                Delete
              </Button>
            ) : (
              <>
                <Button type="button" variant="destructive" onClick={() => void onDelete()} disabled={removeMeal.isPending}>
                  Confirm delete
                </Button>
                <Button type="button" variant="ghost" onClick={() => setConfirmDelete(false)}>
                  Cancel
                </Button>
              </>
            )}
          </div>
        }
      />
      {meal.notes && <p className="surface-card p-4 text-sm">{meal.notes}</p>}
      <div className="grid gap-3 sm:grid-cols-3">
        <Stat label="Calories" value={`${formatGrams(meal.totals.calories)} kcal`} />
        <Stat label="Protein" value={`${formatGrams(meal.totals.protein)} g`} />
        <Stat label="Carbs" value={`${formatGrams(meal.totals.carbohydrates)} g`} />
        <Stat label="Fat" value={`${formatGrams(meal.totals.fat)} g`} />
        <Stat label="Fiber" value={`${formatGrams(meal.totals.fiber)} g`} />
        <Stat label="Sugar" value={`${formatGrams(meal.totals.sugar)} g`} />
      </div>
      <div className="space-y-4">
        {meal.food_entries.map((food) => (
          <article key={food.id} className="surface-card p-4">
            <div className="flex items-baseline justify-between gap-2">
              <h2 className="font-medium">{food.food_name}</h2>
              <p className="text-sm text-muted-foreground">
                {formatGrams(food.quantity)} {food.unit}
              </p>
            </div>
            <p className="mt-2 text-sm text-muted-foreground">
              {formatGrams(food.calories)} kcal · P {formatGrams(food.protein)} · C {formatGrams(food.carbohydrates)} · F{" "}
              {formatGrams(food.fat)}
            </p>
            {food.micronutrients.length > 0 && (
              <ul className="mt-3 grid gap-1 text-sm sm:grid-cols-2">
                {food.micronutrients.map((micro) => (
                  <li key={micro.id ?? micro.nutrient_name}>
                    {micro.nutrient_name}: {formatGrams(micro.amount)} {micro.unit}
                  </li>
                ))}
              </ul>
            )}
          </article>
        ))}
      </div>
      <Button asChild variant="ghost">
        <Link to="/meals">Back to meals</Link>
      </Button>
    </section>
  );
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="surface-card p-4">
      <p className="text-sm text-muted-foreground">{label}</p>
      <p className="mt-1 font-medium">{value}</p>
    </div>
  );
}

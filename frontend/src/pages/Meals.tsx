import { FormEvent, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useDeleteMeal, useMeals } from "@/hooks/useMeals";
import { getApiErrorMessage } from "@/api/auth";
import { MEAL_TYPES, type MealListParams, type MealType } from "@/types/meal";
import { MEAL_TYPE_LABELS, formatGrams } from "@/utils/meals";
import { formatDateTime } from "@/utils/datetime";
import { PageHeader } from "@/components/ui/page-header";
import { ErrorAlert } from "@/components/ui/error-alert";
import { EmptyState } from "@/components/ui/empty-state";
import { PageSkeleton } from "@/components/ui/skeleton";
import { usePageTitle } from "@/hooks/usePageTitle";

const selectClass =
  "flex h-10 w-full rounded-[11px] border border-input bg-card px-3 py-2 text-sm focus-visible:outline-none focus-visible:border-sage focus-visible:ring-2 focus-visible:ring-sage/30";

export function Meals() {
  usePageTitle("Meals");
  const [params, setParams] = useSearchParams();
  const [pendingDelete, setPendingDelete] = useState<number | null>(null);
  const filters = useMemo(() => readFilters(params), [params]);
  const mealsQuery = useMeals(filters);
  const removeMeal = useDeleteMeal();

  function updateFilter(next: Partial<MealListParams>) {
    const merged = { ...filters, ...next, page: next.page ?? 1 };
    const search = new URLSearchParams();
    Object.entries(merged).forEach(([key, value]) => {
      if (value !== undefined && value !== "") {
        search.set(key, String(value));
      }
    });
    setParams(search);
  }

  function onFilterSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = new FormData(event.currentTarget);
    updateFilter({
      date: String(form.get("date") ?? ""),
      start_date: String(form.get("start_date") ?? ""),
      end_date: String(form.get("end_date") ?? ""),
      meal_type: (String(form.get("meal_type") ?? "") || "") as MealType | "",
      q: String(form.get("q") ?? ""),
      page: 1,
    });
  }

  const page = filters.page ?? 1;
  const totalPages = mealsQuery.data?.total_pages ?? 0;
  const items = mealsQuery.data?.items ?? [];

  return (
    <section className="space-y-6">
      <PageHeader
        title="Meals"
        description="Filter, search, and page through logged meals."
        actions={
          <Button asChild>
            <Link to="/meals/new">New meal</Link>
          </Button>
        }
      />

      <form className="surface-card grid gap-3 p-4 md:grid-cols-6" onSubmit={onFilterSubmit}>
        <label className="space-y-1 text-sm md:col-span-1">
          <span className="font-medium">Date</span>
          <Input name="date" type="date" defaultValue={filters.date ?? ""} />
        </label>
        <label className="space-y-1 text-sm">
          <span className="font-medium">From</span>
          <Input name="start_date" type="date" defaultValue={filters.start_date ?? ""} />
        </label>
        <label className="space-y-1 text-sm">
          <span className="font-medium">To</span>
          <Input name="end_date" type="date" defaultValue={filters.end_date ?? ""} />
        </label>
        <label className="space-y-1 text-sm">
          <span className="font-medium">Meal type</span>
          <select id="meal_type_filter" name="meal_type" className={selectClass} defaultValue={filters.meal_type ?? ""}>
            <option value="">All</option>
            {MEAL_TYPES.map((type) => (
              <option key={type} value={type}>
                {MEAL_TYPE_LABELS[type]}
              </option>
            ))}
          </select>
        </label>
        <label className="space-y-1 text-sm md:col-span-2">
          <span className="font-medium">Search food</span>
          <Input name="q" placeholder="e.g. oatmeal" defaultValue={filters.q ?? ""} />
        </label>
        <div className="flex items-end gap-2 md:col-span-6">
          <Button type="submit">Apply filters</Button>
          <Button type="button" variant="ghost" onClick={() => setParams(new URLSearchParams())}>
            Reset
          </Button>
        </div>
      </form>

      {mealsQuery.isLoading && <PageSkeleton cards={3} />}
      {mealsQuery.isError && (
        <ErrorAlert
          message={getApiErrorMessage(mealsQuery.error, "Could not load meals")}
          onRetry={() => void mealsQuery.refetch()}
        />
      )}
      {!mealsQuery.isLoading && !mealsQuery.isError && items.length === 0 && (
        <EmptyState title="No meals logged yet">
          Start by adding your first meal to see your nutrition summary.{" "}
          <Link className="text-forest underline underline-offset-2" to="/meals/new">
            Log a meal
          </Link>
        </EmptyState>
      )}

      {items.length > 0 && (
        <>
          <div className="hidden overflow-x-auto rounded-[16px] border border-border md:block">
            <table className="w-full min-w-[720px] text-left text-sm">
              <thead className="bg-muted/60">
                <tr>
                  <th className="px-3 py-2 font-medium">Date</th>
                  <th className="px-3 py-2 font-medium">Meal</th>
                  <th className="px-3 py-2 font-medium">Food</th>
                  <th className="px-3 py-2 font-medium">Qty</th>
                  <th className="px-3 py-2 font-medium">kcal</th>
                  <th className="px-3 py-2 font-medium">P</th>
                  <th className="px-3 py-2 font-medium">C</th>
                  <th className="px-3 py-2 font-medium">F</th>
                  <th className="px-3 py-2 font-medium">Actions</th>
                </tr>
              </thead>
              <tbody>
                {items.map((meal) =>
                  meal.food_entries.map((food, foodIndex) => (
                    <tr key={`${meal.id}-${food.id ?? foodIndex}`} className="border-t">
                      <td className="px-3 py-2 align-top">{foodIndex === 0 ? formatDateTime(meal.consumed_at) : ""}</td>
                      <td className="px-3 py-2 align-top">{foodIndex === 0 ? MEAL_TYPE_LABELS[meal.meal_type] : ""}</td>
                      <td className="px-3 py-2">{food.food_name}</td>
                      <td className="px-3 py-2">
                        {formatGrams(food.quantity)} {food.unit}
                      </td>
                      <td className="px-3 py-2">{formatGrams(food.calories)}</td>
                      <td className="px-3 py-2">{formatGrams(food.protein)}</td>
                      <td className="px-3 py-2">{formatGrams(food.carbohydrates)}</td>
                      <td className="px-3 py-2">{formatGrams(food.fat)}</td>
                      <td className="px-3 py-2 align-top">
                        {foodIndex === 0 && (
                          <MealActions
                            mealId={meal.id}
                            pendingDelete={pendingDelete}
                            onAskDelete={setPendingDelete}
                            onConfirm={() => {
                              void removeMeal.mutateAsync(meal.id).then(() => setPendingDelete(null));
                            }}
                          />
                        )}
                      </td>
                    </tr>
                  )),
                )}
              </tbody>
            </table>
          </div>

          <div className="space-y-3 md:hidden">
            {items.map((meal) => (
              <article key={meal.id} className="surface-card p-4">
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <p className="font-medium">{MEAL_TYPE_LABELS[meal.meal_type]}</p>
                    <p className="text-sm text-muted-foreground">{formatDateTime(meal.consumed_at)}</p>
                  </div>
                  <p className="text-sm">{formatGrams(meal.totals.calories)} kcal</p>
                </div>
                <ul className="mt-3 space-y-1 text-sm">
                  {meal.food_entries.map((food, foodIndex) => (
                    <li key={food.id ?? foodIndex}>
                      {food.food_name} · {formatGrams(food.quantity)} {food.unit} · {formatGrams(food.calories)} kcal
                    </li>
                  ))}
                </ul>
                <div className="mt-3">
                  <MealActions
                    mealId={meal.id}
                    pendingDelete={pendingDelete}
                    onAskDelete={setPendingDelete}
                    onConfirm={() => {
                      void removeMeal.mutateAsync(meal.id).then(() => setPendingDelete(null));
                    }}
                  />
                </div>
              </article>
            ))}
          </div>

          {totalPages > 1 && (
            <div className="flex items-center justify-between text-sm">
              <Button
                type="button"
                variant="outline"
                disabled={page <= 1}
                onClick={() => updateFilter({ page: page - 1 })}
              >
                Previous
              </Button>
              <span>
                Page {page} of {totalPages}
              </span>
              <Button
                type="button"
                variant="outline"
                disabled={page >= totalPages}
                onClick={() => updateFilter({ page: page + 1 })}
              >
                Next
              </Button>
            </div>
          )}
        </>
      )}
    </section>
  );
}

function MealActions({
  mealId,
  pendingDelete,
  onAskDelete,
  onConfirm,
}: {
  mealId: number;
  pendingDelete: number | null;
  onAskDelete: (id: number | null) => void;
  onConfirm: () => void;
}) {
  if (pendingDelete === mealId) {
    return (
      <div className="flex flex-wrap gap-2">
        <Button type="button" size="sm" variant="destructive" onClick={onConfirm}>
          Confirm delete
        </Button>
        <Button type="button" size="sm" variant="ghost" onClick={() => onAskDelete(null)}>
          Cancel
        </Button>
      </div>
    );
  }
  return (
    <div className="flex flex-wrap gap-2">
      <Button asChild size="sm" variant="ghost">
        <Link to={`/meals/${mealId}`}>View</Link>
      </Button>
      <Button asChild size="sm" variant="ghost">
        <Link to={`/meals/${mealId}/edit`}>Edit</Link>
      </Button>
      <Button type="button" size="sm" variant="ghost" onClick={() => onAskDelete(mealId)}>
        Delete
      </Button>
    </div>
  );
}

function readFilters(params: URLSearchParams): MealListParams {
  const page = Number(params.get("page") ?? "1");
  const mealType = params.get("meal_type") ?? "";
  return {
    page: Number.isFinite(page) && page > 0 ? page : 1,
    page_size: 20,
    date: params.get("date") ?? "",
    start_date: params.get("start_date") ?? "",
    end_date: params.get("end_date") ?? "",
    meal_type: MEAL_TYPES.includes(mealType as MealType) ? (mealType as MealType) : "",
    q: params.get("q") ?? "",
  };
}

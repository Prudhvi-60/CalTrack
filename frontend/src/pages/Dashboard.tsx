import { Link } from "react-router-dom";
import { MacroProgress } from "@/components/nutrition/MacroProgress";
import { CalorieTrendChart } from "@/components/charts/CalorieTrendChart";
import { MacroDistributionChart } from "@/components/charts/MacroDistributionChart";
import { GoalComparisonChart } from "@/components/charts/GoalComparisonChart";
import { TodayMeals } from "@/components/dashboard/TodayMeals";
import { RecentFoods } from "@/components/dashboard/RecentFoods";
import { useDailyNutrition, useGoalComparison, useWeeklyNutrition } from "@/hooks/useNutrition";
import { getApiErrorMessage } from "@/api/auth";
import { Button } from "@/components/ui/button";
import { PageHeader } from "@/components/ui/page-header";
import { ErrorAlert } from "@/components/ui/error-alert";
import { EmptyState } from "@/components/ui/empty-state";
import { PageSkeleton, Skeleton } from "@/components/ui/skeleton";
import { usePageTitle } from "@/hooks/usePageTitle";

export function Dashboard() {
  usePageTitle("Dashboard");
  const dailyQuery = useDailyNutrition();
  const weeklyQuery = useWeeklyNutrition();
  const comparisonQuery = useGoalComparison();

  const isLoading = dailyQuery.isLoading || weeklyQuery.isLoading || comparisonQuery.isLoading;
  const error = dailyQuery.error ?? weeklyQuery.error ?? comparisonQuery.error;

  const daily = dailyQuery.data;
  const remaining = daily?.remaining;
  const goals = daily?.goals;

  return (
    <section className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Today’s intake, remaining macros, and weekly trend from the API."
        actions={
          <Button asChild>
            <Link to="/meals/new">Log meal</Link>
          </Button>
        }
      />

      {isLoading && (
        <div className="space-y-4">
          <PageSkeleton />
          <Skeleton className="h-64" />
        </div>
      )}
      {error && (
        <ErrorAlert
          message={getApiErrorMessage(error, "Could not load dashboard")}
          onRetry={() => {
            void dailyQuery.refetch();
            void weeklyQuery.refetch();
            void comparisonQuery.refetch();
          }}
        />
      )}

      {daily && !goals && (
        <EmptyState title="No goals yet">
          Set calorie and macro targets to see remaining values.{" "}
          <Link className="text-primary underline" to="/goals">
            Open goals
          </Link>
        </EmptyState>
      )}

      {daily && (
        <div className="grid gap-4 sm:grid-cols-2">
          <MacroProgress
            label="Calories"
            actual={daily.totals.calories}
            target={goals?.daily_calorie_target ?? 0}
            remaining={remaining?.calories ?? 0}
            unit="kcal"
          />
          <MacroProgress
            label="Protein"
            actual={daily.totals.protein}
            target={goals?.protein_target ?? 0}
            remaining={remaining?.protein ?? 0}
            unit="g"
          />
          <MacroProgress
            label="Carbohydrates"
            actual={daily.totals.carbohydrates}
            target={goals?.carb_target ?? 0}
            remaining={remaining?.carbohydrates ?? 0}
            unit="g"
          />
          <MacroProgress
            label="Fat"
            actual={daily.totals.fat}
            target={goals?.fat_target ?? 0}
            remaining={remaining?.fat ?? 0}
            unit="g"
          />
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <article className="rounded-lg border bg-card p-4">
          <h2 className="text-sm font-medium">Weekly calorie trend</h2>
          {weeklyQuery.data && <CalorieTrendChart days={weeklyQuery.data.days} />}
        </article>
        <article className="rounded-lg border bg-card p-4">
          <h2 className="text-sm font-medium">Macro breakdown</h2>
          {daily && <MacroDistributionChart totals={daily.totals} />}
        </article>
      </div>

      <article className="rounded-lg border bg-card p-4">
        <h2 className="text-sm font-medium">Goal vs actual</h2>
        {comparisonQuery.data &&
          (comparisonQuery.data.has_goals ? (
            <GoalComparisonChart items={comparisonQuery.data.items} />
          ) : (
            <p className="mt-3 text-sm text-muted-foreground">No goals set yet.</p>
          ))}
      </article>

      <div className="grid gap-4 lg:grid-cols-2">
        <article className="rounded-lg border bg-card p-4">
          <h2 className="text-sm font-medium">Today’s meals</h2>
          <div className="mt-3">{daily && <TodayMeals meals={daily.meals} />}</div>
        </article>
        <article className="rounded-lg border bg-card p-4">
          <h2 className="text-sm font-medium">Recent food entries</h2>
          <div className="mt-3">{daily && <RecentFoods foods={daily.recent_foods} />}</div>
        </article>
      </div>
    </section>
  );
}

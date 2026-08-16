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
import { Card } from "@/components/ui/card";
import { PageHeader } from "@/components/ui/page-header";
import { ErrorAlert } from "@/components/ui/error-alert";
import { EmptyState } from "@/components/ui/empty-state";
import { PageSkeleton, Skeleton } from "@/components/ui/skeleton";
import { usePageTitle } from "@/hooks/usePageTitle";
import { formatGrams } from "@/utils/meals";

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
    <section className="space-y-8">
      <PageHeader
        title="Dashboard"
        description="A calm daily overview of calories, macros, meals, and progress toward your goals."
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
          <Link className="text-forest underline underline-offset-2" to="/goals">
            Open goals
          </Link>
        </EmptyState>
      )}

      {daily && (
        <div>
          <h2 className="mb-3 text-sm font-semibold text-foreground">Nutrition statistics</h2>
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
          <p className="mt-3 text-sm text-muted-foreground">
            Fiber today: <span className="font-medium tabular-nums text-foreground">{formatGrams(daily.totals.fiber)} g</span>
          </p>
        </div>
      )}

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="text-sm font-semibold">Weekly calorie trend</h2>
          {weeklyQuery.data && <CalorieTrendChart days={weeklyQuery.data.days} />}
        </Card>
        <Card>
          <h2 className="text-sm font-semibold">Macro breakdown</h2>
          {daily && <MacroDistributionChart totals={daily.totals} />}
        </Card>
      </div>

      <Card>
        <h2 className="text-sm font-semibold">Goals and progress</h2>
        {comparisonQuery.data &&
          (comparisonQuery.data.has_goals ? (
            <GoalComparisonChart items={comparisonQuery.data.items} />
          ) : (
            <p className="mt-3 text-sm text-muted-foreground">No goals set yet.</p>
          ))}
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <h2 className="text-sm font-semibold">Today’s meals</h2>
          <div className="mt-3">{daily && <TodayMeals meals={daily.meals} />}</div>
        </Card>
        <Card>
          <h2 className="text-sm font-semibold">Recent food entries</h2>
          <div className="mt-3">{daily && <RecentFoods foods={daily.recent_foods} />}</div>
        </Card>
      </div>
    </section>
  );
}

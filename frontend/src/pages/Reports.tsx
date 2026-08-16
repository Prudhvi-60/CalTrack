import { useSearchParams } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { CalorieTrendChart } from "@/components/charts/CalorieTrendChart";
import { MacroTrendChart } from "@/components/charts/MacroTrendChart";
import { MacroBarChart } from "@/components/charts/MacroBarChart";
import { MacroDistributionChart } from "@/components/charts/MacroDistributionChart";
import { GoalComparisonChart } from "@/components/charts/GoalComparisonChart";
import { MicronutrientPanel } from "@/components/nutrition/MicronutrientPanel";
import { useGoalComparison, useMicronutrients, useNutritionTrends } from "@/hooks/useNutrition";
import { getApiErrorMessage } from "@/api/auth";
import type { ReportRange } from "@/api/nutrition";
import { PageHeader } from "@/components/ui/page-header";
import { ErrorAlert } from "@/components/ui/error-alert";
import { PageSkeleton, Skeleton } from "@/components/ui/skeleton";
import { usePageTitle } from "@/hooks/usePageTitle";

const RANGES: ReportRange[] = [7, 30, 90];

function parseRange(value: string | null): ReportRange {
  const parsed = Number(value);
  return parsed === 30 || parsed === 90 ? parsed : 7;
}

export function Reports() {
  usePageTitle("Reports");
  const [params, setParams] = useSearchParams();
  const days = parseRange(params.get("days"));
  const trendsQuery = useNutritionTrends(days);
  const comparisonQuery = useGoalComparison(days);
  const microsQuery = useMicronutrients(days);

  const isLoading = trendsQuery.isLoading || comparisonQuery.isLoading || microsQuery.isLoading;
  const error = trendsQuery.error ?? comparisonQuery.error ?? microsQuery.error;
  const totals = trendsQuery.data?.totals;

  return (
    <section className="space-y-6">
      <PageHeader
        title="Reports"
        description="Calorie trends, macros, goal comparison, and micronutrients for the selected period."
        actions={
          <div className="flex flex-wrap rounded-[12px] border border-border bg-card p-1" role="group" aria-label="Time range">
            {RANGES.map((range) => (
              <Button
                key={range}
                type="button"
                size="sm"
                variant={days === range ? "default" : "ghost"}
                aria-pressed={days === range}
                onClick={() => setParams({ days: String(range) })}
              >
                {range} days
              </Button>
            ))}
          </div>
        }
      />

      {isLoading && (
        <div className="space-y-4">
          <PageSkeleton cards={2} />
          <Skeleton className="h-64" />
        </div>
      )}
      {error && (
        <ErrorAlert
          message={getApiErrorMessage(error, "Could not load reports")}
          onRetry={() => {
            void trendsQuery.refetch();
            void comparisonQuery.refetch();
            void microsQuery.refetch();
          }}
        />
      )}

      <article className="surface-card p-4 sm:p-5">
        <h2 className="text-sm font-medium">Calories</h2>
        {trendsQuery.data && <CalorieTrendChart days={trendsQuery.data.items} />}
      </article>

      <article className="surface-card p-4 sm:p-5">
        <h2 className="text-sm font-medium">Protein, carbs, and fat</h2>
        {trendsQuery.data && <MacroTrendChart days={trendsQuery.data.items} />}
      </article>

      <div className="grid gap-4 lg:grid-cols-2">
        <article className="surface-card p-4 sm:p-5">
          <h2 className="text-sm font-medium">Macronutrients</h2>
          {totals && <MacroBarChart totals={totals} />}
        </article>
        <article className="surface-card p-4 sm:p-5">
          <h2 className="text-sm font-medium">Macro distribution</h2>
          {totals && <MacroDistributionChart totals={totals} emptyMessage="No macros logged in this range." />}
        </article>
      </div>

      <article className="surface-card p-4 sm:p-5">
        <h2 className="text-sm font-medium">Goal vs actual</h2>
        {comparisonQuery.data &&
          (comparisonQuery.data.has_goals ? (
            <GoalComparisonChart items={comparisonQuery.data.items} />
          ) : (
            <p className="mt-3 text-sm text-muted-foreground">Set goals to compare intake against targets.</p>
          ))}
      </article>

      <article className="surface-card p-4 sm:p-5">
        <h2 className="text-sm font-medium">Micronutrients</h2>
        <p className="mt-1 text-xs text-muted-foreground">Totals for the selected range from logged meals.</p>
        <div className="mt-3">{microsQuery.data && <MicronutrientPanel items={microsQuery.data.items} />}</div>
      </article>
    </section>
  );
}

import { useEffect, useState } from "react";
import { useForm, type Resolver } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { MacroProgress } from "@/components/nutrition/MacroProgress";
import { useCreateGoal, useDeleteGoal, useGoals, useReplaceGoal } from "@/hooks/useGoals";
import { getApiErrorMessage } from "@/api/auth";
import { goalSchema, type GoalFormValues } from "@/schemas/goals";
import type { GoalPayload } from "@/types/goal";
import { PageHeader } from "@/components/ui/page-header";
import { ErrorAlert } from "@/components/ui/error-alert";
import { EmptyState } from "@/components/ui/empty-state";
import { PageSkeleton } from "@/components/ui/skeleton";
import { Field } from "@/components/ui/field";
import { usePageTitle } from "@/hooks/usePageTitle";

const emptyValues: GoalFormValues = {
  daily_calorie_target: 2200,
  protein_target: 130,
  carb_target: 250,
  fat_target: 70,
  weight_goal: 72,
};

function toPayload(values: GoalFormValues): GoalPayload {
  return {
    daily_calorie_target: values.daily_calorie_target,
    protein_target: values.protein_target,
    carb_target: values.carb_target,
    fat_target: values.fat_target,
    weight_goal: values.weight_goal,
  };
}

export function Goals() {
  usePageTitle("Goals");
  const goalsQuery = useGoals();
  const createGoal = useCreateGoal();
  const replaceGoal = useReplaceGoal();
  const removeGoal = useDeleteGoal();
  const [serverError, setServerError] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);

  const current = goalsQuery.data?.items[0];

  const form = useForm<GoalFormValues>({
    resolver: zodResolver(goalSchema) as Resolver<GoalFormValues>,
    defaultValues: emptyValues,
  });

  useEffect(() => {
    if (!current) {
      return;
    }
    form.reset({
      daily_calorie_target: current.daily_calorie_target,
      protein_target: current.protein_target,
      carb_target: current.carb_target,
      fat_target: current.fat_target,
      weight_goal: current.weight_goal,
    });
  }, [current, form]);

  async function onSubmit(values: GoalFormValues) {
    setServerError(null);
    try {
      const payload = toPayload(values);
      if (current) {
        await replaceGoal.mutateAsync(payload);
      } else {
        await createGoal.mutateAsync(payload);
      }
    } catch (error) {
      setServerError(getApiErrorMessage(error, "Could not save goals"));
    }
  }

  async function onDelete() {
    setServerError(null);
    try {
      await removeGoal.mutateAsync();
      form.reset(emptyValues);
      setConfirmDelete(false);
    } catch (error) {
      setServerError(getApiErrorMessage(error, "Could not delete goals"));
    }
  }

  const saving = createGoal.isPending || replaceGoal.isPending;

  return (
    <section className="space-y-6">
      <PageHeader
        title="Goals"
        description="Set daily calorie and macro targets. Progress uses today’s logged meals from the API."
      />

      {goalsQuery.isLoading && <PageSkeleton />}

      {goalsQuery.isError && (
        <ErrorAlert
          message={getApiErrorMessage(goalsQuery.error, "Could not load goals")}
          onRetry={() => void goalsQuery.refetch()}
        />
      )}

      {current && (
        <div className="grid gap-4 sm:grid-cols-2">
          <MacroProgress
            label="Calories"
            actual={current.calories_actual}
            target={current.daily_calorie_target}
            remaining={current.calories_remaining}
            unit="kcal"
          />
          <MacroProgress
            label="Protein"
            actual={current.protein_actual}
            target={current.protein_target}
            remaining={current.protein_remaining}
            unit="g"
          />
          <MacroProgress
            label="Carbohydrates"
            actual={current.carb_actual}
            target={current.carb_target}
            remaining={current.carb_remaining}
            unit="g"
          />
          <MacroProgress
            label="Fat"
            actual={current.fat_actual}
            target={current.fat_target}
            remaining={current.fat_remaining}
            unit="g"
          />
        </div>
      )}

      {!goalsQuery.isLoading && !current && !goalsQuery.isError && (
        <EmptyState title="No goals yet">
          Enter daily calorie and macro targets to start tracking progress.
        </EmptyState>
      )}

      <form className="surface-card max-w-xl space-y-4 p-6" onSubmit={form.handleSubmit(onSubmit)} noValidate>
        <h2 className="text-lg font-medium">{current ? "Update targets" : "Create targets"}</h2>
        <Field label="Daily calories (kcal)" id="daily_calorie_target" error={form.formState.errors.daily_calorie_target?.message}>
          <Input id="daily_calorie_target" type="number" min={0} step="1" {...form.register("daily_calorie_target")} />
        </Field>
        <Field label="Protein (g)" id="protein_target" error={form.formState.errors.protein_target?.message}>
          <Input id="protein_target" type="number" min={0} step="0.1" {...form.register("protein_target")} />
        </Field>
        <Field label="Carbohydrates (g)" id="carb_target" error={form.formState.errors.carb_target?.message}>
          <Input id="carb_target" type="number" min={0} step="0.1" {...form.register("carb_target")} />
        </Field>
        <Field label="Fat (g)" id="fat_target" error={form.formState.errors.fat_target?.message}>
          <Input id="fat_target" type="number" min={0} step="0.1" {...form.register("fat_target")} />
        </Field>
        <Field label="Weight goal (kg, optional)" id="weight_goal" error={form.formState.errors.weight_goal?.message}>
          <Input id="weight_goal" type="number" min={0} step="0.1" {...form.register("weight_goal")} />
        </Field>
        {current?.weight_goal != null && (
          <p className="text-sm text-muted-foreground">Current weight goal: {current.weight_goal} kg</p>
        )}
        {serverError && <ErrorAlert message={serverError} />}
        <div className="flex flex-wrap gap-3">
          <Button type="submit" disabled={saving}>
            {saving ? "Saving…" : current ? "Save changes" : "Save goals"}
          </Button>
          {current && !confirmDelete && (
            <Button type="button" variant="outline" onClick={() => setConfirmDelete(true)}>
              Delete goals
            </Button>
          )}
          {current && confirmDelete && (
            <>
              <Button type="button" variant="destructive" onClick={onDelete} disabled={removeGoal.isPending}>
                {removeGoal.isPending ? "Deleting…" : "Confirm delete"}
              </Button>
              <Button type="button" variant="ghost" onClick={() => setConfirmDelete(false)}>
                Cancel
              </Button>
            </>
          )}
        </div>
      </form>
    </section>
  );
}


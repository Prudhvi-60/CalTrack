import { useFieldArray, useForm, type Resolver, type UseFormReturn } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field } from "@/components/ui/field";
import { ErrorAlert } from "@/components/ui/error-alert";
import { mealSchema, type MealFormValues } from "@/schemas/meal";
import { emptyFoodEntry } from "@/components/meals/emptyFoodEntry";
import { MEAL_TYPES, NUTRIENT_NAMES, type MealPayload } from "@/types/meal";
import { MEAL_TYPE_LABELS } from "@/utils/meals";
import { fromDateTimeLocal } from "@/utils/datetime";
import { cn } from "@/utils/cn";

const selectClass =
  "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring";

type MealFormProps = {
  defaultValues: MealFormValues;
  submitLabel: string;
  onSubmit: (payload: MealPayload) => Promise<void>;
  serverError?: string | null;
  isSubmitting?: boolean;
};

export function MealForm({ defaultValues, submitLabel, onSubmit, serverError, isSubmitting }: MealFormProps) {
  const form = useForm<MealFormValues>({
    resolver: zodResolver(mealSchema) as Resolver<MealFormValues>,
    defaultValues,
  });
  const foods = useFieldArray({ control: form.control, name: "food_entries" });

  async function handleSubmit(values: MealFormValues) {
    await onSubmit({
      meal_type: values.meal_type,
      consumed_at: fromDateTimeLocal(values.consumed_at),
      notes: values.notes?.trim() ? values.notes.trim() : null,
      food_entries: values.food_entries.map((entry) => ({
        ...entry,
        micronutrients: entry.micronutrients ?? [],
      })),
    });
  }

  return (
    <form className="space-y-6" onSubmit={form.handleSubmit(handleSubmit)} noValidate>
      <div className="grid gap-4 sm:grid-cols-2">
        <Field label="Meal type" id="meal_type">
          <select id="meal_type" className={selectClass} {...form.register("meal_type")}>
            {MEAL_TYPES.map((type) => (
              <option key={type} value={type}>
                {MEAL_TYPE_LABELS[type]}
              </option>
            ))}
          </select>
        </Field>
        <Field label="Date and time" id="consumed_at" error={form.formState.errors.consumed_at?.message}>
          <Input id="consumed_at" type="datetime-local" {...form.register("consumed_at")} />
        </Field>
      </div>
      <Field label="Notes" id="notes">
        <textarea id="notes" rows={3} className={cn(selectClass, "h-auto py-2")} {...form.register("notes")} />
      </Field>

      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-lg font-medium">Foods</h2>
          <Button type="button" variant="secondary" onClick={() => foods.append(emptyFoodEntry)}>
            Add food
          </Button>
        </div>
        {form.formState.errors.food_entries?.root && (
          <p className="text-sm text-destructive" role="alert">
            {form.formState.errors.food_entries.root.message}
          </p>
        )}
        {form.formState.errors.food_entries?.message && (
          <p className="text-sm text-destructive" role="alert">
            {form.formState.errors.food_entries.message}
          </p>
        )}
        {foods.fields.map((field, index) => (
          <FoodFields
            key={field.id}
            index={index}
            form={form}
            canRemove={foods.fields.length > 1}
            onRemove={() => foods.remove(index)}
          />
        ))}
      </div>

      {serverError && <ErrorAlert message={serverError} />}
      <Button type="submit" disabled={isSubmitting}>
        {isSubmitting ? "Saving…" : submitLabel}
      </Button>
    </form>
  );
}

function FoodFields({
  index,
  form,
  canRemove,
  onRemove,
}: {
  index: number;
  form: UseFormReturn<MealFormValues>;
  canRemove: boolean;
  onRemove: () => void;
}) {
  const micros = useFieldArray({ control: form.control, name: `food_entries.${index}.micronutrients` });
  const errors = form.formState.errors.food_entries?.[index];

  return (
    <div className="space-y-4 rounded-lg border bg-card p-4">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium">Food {index + 1}</h3>
        {canRemove && (
          <Button type="button" variant="ghost" size="sm" onClick={onRemove}>
            Remove
          </Button>
        )}
      </div>
      <div className="grid gap-3 sm:grid-cols-2">
        <Field label="Food name" id={`food-${index}-name`} error={errors?.food_name?.message}>
          <Input id={`food-${index}-name`} {...form.register(`food_entries.${index}.food_name`)} />
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Quantity" id={`food-${index}-qty`} error={errors?.quantity?.message}>
            <Input id={`food-${index}-qty`} type="number" min={0} step="0.1" {...form.register(`food_entries.${index}.quantity`)} />
          </Field>
          <Field label="Unit" id={`food-${index}-unit`} error={errors?.unit?.message}>
            <Input id={`food-${index}-unit`} list="food-units" {...form.register(`food_entries.${index}.unit`)} />
          </Field>
        </div>
      </div>
      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
        <Field label="Calories" id={`food-${index}-cal`} error={errors?.calories?.message}>
          <Input id={`food-${index}-cal`} type="number" min={0} step="0.1" {...form.register(`food_entries.${index}.calories`)} />
        </Field>
        <Field label="Protein (g)" id={`food-${index}-pro`} error={errors?.protein?.message}>
          <Input id={`food-${index}-pro`} type="number" min={0} step="0.1" {...form.register(`food_entries.${index}.protein`)} />
        </Field>
        <Field label="Carbs (g)" id={`food-${index}-carb`} error={errors?.carbohydrates?.message}>
          <Input id={`food-${index}-carb`} type="number" min={0} step="0.1" {...form.register(`food_entries.${index}.carbohydrates`)} />
        </Field>
        <Field label="Fat (g)" id={`food-${index}-fat`} error={errors?.fat?.message}>
          <Input id={`food-${index}-fat`} type="number" min={0} step="0.1" {...form.register(`food_entries.${index}.fat`)} />
        </Field>
        <Field label="Fiber (g)" id={`food-${index}-fiber`} error={errors?.fiber?.message}>
          <Input id={`food-${index}-fiber`} type="number" min={0} step="0.1" {...form.register(`food_entries.${index}.fiber`)} />
        </Field>
        <Field label="Sugar (g)" id={`food-${index}-sugar`} error={errors?.sugar?.message}>
          <Input id={`food-${index}-sugar`} type="number" min={0} step="0.1" {...form.register(`food_entries.${index}.sugar`)} />
        </Field>
      </div>
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium">Micronutrients</p>
          <Button
            type="button"
            variant="secondary"
            size="sm"
            onClick={() => micros.append({ nutrient_name: "Vitamin C", amount: 0, unit: "mg" })}
          >
            Add nutrient
          </Button>
        </div>
        {micros.fields.map((micro, microIndex) => (
          <div key={micro.id} className="grid gap-2 sm:grid-cols-[1fr_6rem_5rem_auto]">
            <select
              className={selectClass}
              aria-label={`Nutrient name ${microIndex + 1}`}
              {...form.register(`food_entries.${index}.micronutrients.${microIndex}.nutrient_name`)}
            >
              {NUTRIENT_NAMES.map((name) => (
                <option key={name} value={name}>
                  {name}
                </option>
              ))}
            </select>
            <Input
              type="number"
              min={0}
              step="0.1"
              aria-label={`Nutrient amount ${microIndex + 1}`}
              {...form.register(`food_entries.${index}.micronutrients.${microIndex}.amount`)}
            />
            <Input
              aria-label={`Nutrient unit ${microIndex + 1}`}
              {...form.register(`food_entries.${index}.micronutrients.${microIndex}.unit`)}
            />
            <Button type="button" variant="ghost" size="sm" onClick={() => micros.remove(microIndex)}>
              Remove
            </Button>
          </div>
        ))}
      </div>
      <datalist id="food-units">
        <option value="g" />
        <option value="ml" />
        <option value="cup" />
        <option value="bowl" />
        <option value="plate" />
        <option value="serving" />
        <option value="piece" />
        <option value="tbsp" />
      </datalist>
    </div>
  );
}


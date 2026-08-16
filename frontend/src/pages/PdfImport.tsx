import { FormEvent, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import {
  confirmMealPlan,
  MEAL_SLOTS,
  previewMealPlan,
  type MealPlanConfirmFood,
  type MealPlanDay,
  type MealPlanFood,
  type MealSlot,
} from "@/api/importPdf";
import { getApiErrorMessage } from "@/api/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/ui/page-header";
import { ErrorAlert } from "@/components/ui/error-alert";
import { EmptyState } from "@/components/ui/empty-state";
import { usePageTitle } from "@/hooks/usePageTitle";
import { SLOT_ACCENT } from "@/utils/accents";

const STAGES = [
  "Processing document...",
  "Extracting text...",
  "Identifying meals...",
  "Matching foods...",
  "Preparing your meal diary...",
];

type ReviewFood = MealPlanFood & { slot: MealSlot; include: boolean; id: string };
type ReviewDay = {
  key: string;
  day: number | null;
  date: string;
  label: string | null;
  include: boolean;
  foods: ReviewFood[];
};

function emptyFood(slot: MealSlot): ReviewFood {
  return {
    id: `new-${crypto.randomUUID()}`,
    slot,
    include: true,
    food: "",
    quantity: null,
    quantity_text: null,
    unit: "",
    notes: "",
    original_label: null,
    meal_name: null,
    alternative: null,
    nutrition_status: "unknown",
    matched_food: null,
    calories: null,
    protein: null,
    carbohydrates: null,
    fat: null,
    fiber: null,
    sugar: null,
  };
}

function toReview(previewDays: MealPlanDay[]): ReviewDay[] {
  return previewDays.map((day, index) => {
    const foods: ReviewFood[] = [];
    for (const slot of MEAL_SLOTS) {
      for (const item of day.meals[slot.id] || []) {
        foods.push({ ...item, slot: slot.id, include: true, id: `${index}-${slot.id}-${foods.length}` });
      }
    }
    return {
      key: `day-${index}`,
      day: day.day,
      date: day.date || new Date().toISOString().slice(0, 10),
      label: day.label,
      include: true,
      foods,
    };
  });
}

export function PdfImport() {
  usePageTitle("Import food diary");
  const [days, setDays] = useState<ReviewDay[] | null>(null);
  const [summary, setSummary] = useState<{ title: string | null; days: number; meals: number; foods: number } | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [stage, setStage] = useState(STAGES[0]);
  const [reviewOpen, setReviewOpen] = useState(false);
  const [fileName, setFileName] = useState<string | null>(null);

  const totals = useMemo(() => {
    if (!days) {
      return { days: 0, meals: 0, foods: 0 };
    }
    const included = days.filter((day) => day.include);
    const foods = included.flatMap((day) => day.foods.filter((food) => food.include && food.food.trim()));
    const meals = new Set(foods.map((food) => `${food.slot}`)).size;
    return { days: included.length, meals, foods: foods.length };
  }, [days]);

  async function onFile(file: File | null) {
    setError(null);
    setResult(null);
    setDays(null);
    setSummary(null);
    setReviewOpen(false);
    setFileName(null);
    if (!file) {
      return;
    }
    setFileName(file.name);
    if (file.type !== "application/pdf" && !file.name.toLowerCase().endsWith(".pdf")) {
      setError("Upload a PDF file.");
      return;
    }
    setBusy(true);
    let tick = 0;
    const timer = window.setInterval(() => {
      tick += 1;
      setStage(STAGES[tick % STAGES.length]);
    }, 900);
    try {
      setStage("Extracting your meals...");
      const preview = await previewMealPlan(file);
      setDays(toReview(preview.days));
      setSummary({
        title: preview.title,
        days: preview.days_detected,
        meals: preview.meals_detected,
        foods: preview.foods_detected,
      });
    } catch (err) {
      setError(getApiErrorMessage(err, "Could not extract meals from this PDF"));
    } finally {
      window.clearInterval(timer);
      setBusy(false);
    }
  }

  function updateDay(key: string, patch: Partial<ReviewDay>) {
    setDays((current) => current?.map((day) => (day.key === key ? { ...day, ...patch } : day)) ?? null);
  }

  function updateFood(dayKey: string, foodId: string, patch: Partial<ReviewFood>) {
    setDays(
      (current) =>
        current?.map((day) =>
          day.key === dayKey
            ? { ...day, foods: day.foods.map((food) => (food.id === foodId ? { ...food, ...patch } : food)) }
            : day,
        ) ?? null,
    );
  }

  function removeFood(dayKey: string, foodId: string) {
    setDays(
      (current) =>
        current?.map((day) => (day.key === dayKey ? { ...day, foods: day.foods.filter((food) => food.id !== foodId) } : day)) ??
        null,
    );
  }

  function addFood(dayKey: string, slot: MealSlot) {
    setDays(
      (current) =>
        current?.map((day) => (day.key === dayKey ? { ...day, foods: [...day.foods, emptyFood(slot)] } : day)) ?? null,
    );
  }

  async function onConfirm(event?: FormEvent, onlyKey?: string) {
    event?.preventDefault();
    if (!days) {
      return;
    }
    const selected = days.filter((day) => (onlyKey ? day.key === onlyKey : day.include));
    const payload = selected
      .map((day) => ({
        day: day.day,
        date: day.date,
        label: day.label,
        include: true,
        foods: day.foods
          .filter((food) => food.include && food.food.trim())
          .map((food): MealPlanConfirmFood => ({
            food: food.food.trim(),
            quantity: food.quantity,
            unit: food.unit,
            notes: food.notes,
            original_label: food.original_label,
            meal_name: food.meal_name,
            alternative: food.alternative,
            nutrition_status: food.nutrition_status,
            calories: food.calories,
            protein: food.protein,
            carbohydrates: food.carbohydrates,
            fat: food.fat,
            fiber: food.fiber,
            sugar: food.sugar,
            slot: food.slot,
            include: true,
          })),
      }))
      .filter((day) => day.foods.length > 0);
    if (payload.length === 0) {
      setError("Select at least one food to import.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const imported = await confirmMealPlan(payload);
      setResult(`Imported ${imported.imported_foods} foods across ${imported.imported_meals} meals.`);
    } catch (err) {
      setError(getApiErrorMessage(err, "Could not save imported meals"));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="space-y-6">
      <PageHeader
        title="Import food diary"
        description="Upload a meal plan, food diary or nutrition PDF. Review extracted meals before anything is saved."
      />
      <div className="upload-zone space-y-2">
        <label htmlFor="diary-pdf" className="text-sm font-medium text-forest">
          Upload your meal plan or food diary PDF
        </label>
        <p className="text-xs text-muted-foreground">Import your food diary. PDF meal plans, diaries, scanned pages, and tables. Typical size under 10 MB.</p>
        <input
          id="diary-pdf"
          type="file"
          accept="application/pdf"
          className="mx-auto mt-2 block w-full max-w-full text-sm"
          onChange={(event) => void onFile(event.target.files?.[0] ?? null)}
        />
      </div>
      {fileName && (
        <p className="text-sm text-muted-foreground">
          File: <span className="font-medium text-foreground">{fileName}</span>
          {busy ? " · Processing…" : summary ? " · Ready to review" : ""}
        </p>
      )}
      {busy && <p className="text-sm text-muted-foreground">{stage}</p>}
      {error && <ErrorAlert message={error} />}
      {result && (
        <p className="text-sm">
          {result}{" "}
          <Link className="text-primary underline" to="/meals">
            View meals
          </Link>{" "}
          ·{" "}
          <Link className="text-primary underline" to="/dashboard">
            Dashboard
          </Link>{" "}
          ·{" "}
          <Link className="text-primary underline" to="/chat">
            Ask Chat
          </Link>
        </p>
      )}
      {summary && days && (
        <div className="surface-card space-y-3 p-4">
          <p className="text-sm font-medium">Extraction complete</p>
          {summary.title && <p className="text-sm text-muted-foreground">{summary.title}</p>}
          <ul className="text-sm text-muted-foreground">
            <li>Days detected: {summary.days}</li>
            <li>Meals detected: {summary.meals}</li>
            <li>Foods detected: {summary.foods}</li>
          </ul>
          <Button type="button" onClick={() => setReviewOpen(true)}>
            Review imported meals
          </Button>
        </div>
      )}
      {reviewOpen && days && (
        <form className="space-y-6" onSubmit={(event) => void onConfirm(event)}>
          {days.length === 0 ? (
            <EmptyState title="No meals found">Try another PDF.</EmptyState>
          ) : (
            days.map((day) => (
              <article key={day.key} className="surface-card space-y-4 p-4">
                <div className="flex flex-wrap items-end gap-3">
                  <label className="text-sm">
                    <span className="mb-1 block text-muted-foreground">Day</span>
                    <Input
                      type="number"
                      min={1}
                      value={day.day ?? ""}
                      onChange={(event) =>
                        updateDay(day.key, { day: event.target.value ? Number(event.target.value) : null })
                      }
                    />
                  </label>
                  <label className="text-sm">
                    <span className="mb-1 block text-muted-foreground">Date</span>
                    <Input
                      type="date"
                      value={day.date}
                      onChange={(event) => updateDay(day.key, { date: event.target.value })}
                    />
                  </label>
                  <label className="flex items-center gap-2 text-sm">
                    <input
                      type="checkbox"
                      checked={day.include}
                      onChange={(event) => updateDay(day.key, { include: event.target.checked })}
                    />
                    Include day
                  </label>
                </div>
                {MEAL_SLOTS.map((slot) => {
                  const items = day.foods.filter((food) => food.slot === slot.id);
                  return (
                    <div key={slot.id} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide">
                          <span className={`h-2.5 w-2.5 rounded-full ${SLOT_ACCENT[slot.id]}`} aria-hidden />
                          {slot.label}
                        </h2>
                        <Button type="button" variant="outline" size="sm" onClick={() => addFood(day.key, slot.id)}>
                          Add food
                        </Button>
                      </div>
                      {items.length === 0 && <p className="text-xs text-muted-foreground">No foods</p>}
                      {items.map((food) => (
                        <div key={food.id} className="grid gap-2 rounded-md border p-3 sm:grid-cols-6">
                          <Input
                            className="sm:col-span-2"
                            value={food.food}
                            onChange={(event) => updateFood(day.key, food.id, { food: event.target.value })}
                            aria-label="Food"
                          />
                          <Input
                            type="number"
                            min={0}
                            step="0.01"
                            value={food.quantity ?? ""}
                            onChange={(event) =>
                              updateFood(day.key, food.id, {
                                quantity: event.target.value === "" ? null : Number(event.target.value),
                                nutrition_status: "unknown",
                                calories: null,
                              })
                            }
                            aria-label="Quantity"
                            placeholder="Qty"
                          />
                          <Input
                            value={food.unit ?? ""}
                            onChange={(event) => updateFood(day.key, food.id, { unit: event.target.value })}
                            aria-label="Unit"
                            placeholder="Unit"
                          />
                          <select
                            className="h-10 rounded-[11px] border border-input bg-card px-2 text-sm"
                            value={food.slot}
                            onChange={(event) => updateFood(day.key, food.id, { slot: event.target.value as MealSlot })}
                            aria-label="Meal category"
                          >
                            {MEAL_SLOTS.map((option) => (
                              <option key={option.id} value={option.id}>
                                {option.label}
                              </option>
                            ))}
                          </select>
                          <div className="flex items-center justify-between gap-2 sm:col-span-6">
                            <p className="text-xs text-muted-foreground">
                              {food.nutrition_status === "matched"
                                ? `Matched${food.calories != null ? ` · ${food.calories} kcal` : ""}`
                                : "Nutrition unknown"}
                              {food.original_label ? ` · ${food.original_label}` : ""}
                              {food.meal_name ? ` · ${food.meal_name}` : ""}
                            </p>
                            <Button type="button" variant="ghost" size="sm" onClick={() => removeFood(day.key, food.id)}>
                              Delete
                            </Button>
                          </div>
                        </div>
                      ))}
                    </div>
                  );
                })}
                <Button type="button" variant="secondary" onClick={() => void onConfirm(undefined, day.key)} disabled={busy}>
                  Confirm day
                </Button>
              </article>
            ))
          )}
          <div className="flex flex-wrap items-center gap-3">
            <Button type="submit" disabled={busy}>
              Confirm import
            </Button>
            <p className="text-xs text-muted-foreground">
              {totals.days} day(s), {totals.foods} food(s) selected
            </p>
          </div>
        </form>
      )}
    </section>
  );
}

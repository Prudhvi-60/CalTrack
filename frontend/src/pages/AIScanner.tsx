import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { MealForm } from "@/components/meals/MealForm";
import { useCreateMeal } from "@/hooks/useMeals";
import { analyzeFoodImage, recordAiCorrections } from "@/api/ai";
import { getApiErrorMessage } from "@/api/auth";
import { analysisToFormValues, correctionsFromConfirm } from "@/utils/aiMeal";
import type { AnalysisType, ConfidenceLevel, FoodAnalysis } from "@/types/ai";
import type { MealPayload } from "@/types/meal";
import { PageHeader } from "@/components/ui/page-header";
import { ErrorAlert } from "@/components/ui/error-alert";
import { usePageTitle } from "@/hooks/usePageTitle";

const ACCEPTED = ["image/jpeg", "image/png", "image/webp"];
const MAX_BYTES = 5 * 1024 * 1024;

function confidenceCopy(level: ConfidenceLevel | undefined, value: number | undefined): string {
  const pct = value == null ? "" : `${Math.round(value * 100)}%`;
  if (level === "HIGH") {
    return `High confidence ${pct}`.trim();
  }
  if (level === "LOW") {
    return `Low confidence ${pct} — please check this item`.trim();
  }
  return `Medium confidence ${pct}`.trim();
}

export function AIScanner() {
  usePageTitle("AI scanner");
  const navigate = useNavigate();
  const createMeal = useCreateMeal();
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<string | null>(null);
  const [analysisType, setAnalysisType] = useState<AnalysisType>("food");
  const [analysis, setAnalysis] = useState<FoodAnalysis | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      if (preview) {
        URL.revokeObjectURL(preview);
      }
    };
  }, [preview]);

  function onFileChange(selected: File | null) {
    setError(null);
    setAnalysis(null);
    if (preview) {
      URL.revokeObjectURL(preview);
    }
    if (!selected) {
      setFile(null);
      setPreview(null);
      return;
    }
    if (!ACCEPTED.includes(selected.type)) {
      setError("Use a JPEG, PNG, or WEBP image.");
      setFile(null);
      setPreview(null);
      return;
    }
    if (selected.size > MAX_BYTES) {
      setError("Image must be 5 MB or smaller.");
      setFile(null);
      setPreview(null);
      return;
    }
    setFile(selected);
    setPreview(URL.createObjectURL(selected));
  }

  async function onAnalyze() {
    if (!file) {
      setError("Choose an image first.");
      return;
    }
    setError(null);
    setAnalyzing(true);
    try {
      const result = await analyzeFoodImage(file, analysisType);
      setAnalysis(result);
    } catch (err) {
      setError(getApiErrorMessage(err, "Could not analyze the image"));
    } finally {
      setAnalyzing(false);
    }
  }

  async function onConfirm(payload: MealPayload) {
    if (!analysis) {
      return;
    }
    setSaveError(null);
    try {
      const corrections = correctionsFromConfirm(analysis, payload);
      try {
        await recordAiCorrections(analysis.analysis_type, corrections, analysis.analysis_id);
      } catch {
        // Corrections are optional evaluation data and must not block saving.
      }
      const meal = await createMeal.mutateAsync(payload);
      navigate(`/meals/${meal.id}`);
    } catch (err) {
      setSaveError(getApiErrorMessage(err, "Could not save meal"));
    }
  }

  return (
    <section className="space-y-6">
      <PageHeader
        title="AI food scanner"
        description="Upload a food photo or nutrition label. A multimodal model estimates foods, portions, and nutrition in one pass. Everything is approximate. Review and edit before saving. Nothing is stored until you confirm."
      />

      <div className="space-y-4 rounded-lg border bg-card p-4">
        <fieldset className="space-y-2">
          <legend className="text-sm font-medium">Image type</legend>
          <label className="mr-4 text-sm">
            <input
              type="radio"
              name="analysis_type"
              className="mr-2"
              checked={analysisType === "food"}
              onChange={() => setAnalysisType("food")}
            />
            Food photograph
          </label>
          <label className="text-sm">
            <input
              type="radio"
              name="analysis_type"
              className="mr-2"
              checked={analysisType === "label"}
              onChange={() => setAnalysisType("label")}
            />
            Nutrition label
          </label>
        </fieldset>
        <div className="space-y-2">
          <label htmlFor="food-image" className="text-sm font-medium">
            Image
          </label>
          <input
            id="food-image"
            type="file"
            accept="image/jpeg,image/png,image/webp"
            onChange={(event) => onFileChange(event.target.files?.[0] ?? null)}
          />
        </div>
        {preview && (
          <img src={preview} alt="Selected food or label preview" className="max-h-64 rounded-md border object-contain" />
        )}
        {error && <ErrorAlert message={error} />}
        <Button type="button" onClick={() => void onAnalyze()} disabled={analyzing || !file} aria-busy={analyzing}>
          {analyzing ? "Analyzing…" : "Analyze Food"}
        </Button>
      </div>

      {analysis && (
        <div className="space-y-4">
          <div className="rounded-lg border bg-accent/40 p-4 text-sm">
            <p>
              Overall confidence: <span className="font-medium">{Math.round(analysis.confidence * 100)}%</span>
              {analysis.meal_type ? ` · Suggested meal: ${analysis.meal_type.toLowerCase()}` : ""}
            </p>
            <p className="mt-2 text-muted-foreground">
              These are estimates, not lab measurements. Edit any name, quantity, or nutrient value before saving.
            </p>
            <ul className="mt-3 space-y-2">
              {analysis.food_items.map((item, index) => (
                <li key={`${item.name}-${index}`} className="rounded-md border bg-background/80 p-3">
                  <p className="font-medium">
                    {item.name} · {item.quantity} {item.unit}
                    {item.estimated_weight_g != null ? ` · ~${Math.round(Number(item.estimated_weight_g))} g` : ""}
                  </p>
                  <p className="text-muted-foreground">
                    {confidenceCopy(item.confidence_level, item.confidence)}
                    {item.nutrition_source === "llm" ? " · Estimated nutrition (AI)" : ""}
                    {item.nutrition_source === "database" ? " · Nutrition from food database" : ""}
                    {item.nutrition_source === "label" ? " · Nutrition from label" : ""}
                  </p>
                </li>
              ))}
            </ul>
            <ul className="mt-3 list-disc space-y-1 pl-5 text-muted-foreground">
              {analysis.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          </div>
          <h2 className="text-lg font-medium">Review and confirm</h2>
          <MealForm
            key={`${analysis.food_items[0]?.name}-${analysis.confidence}`}
            defaultValues={analysisToFormValues(analysis)}
            submitLabel="Confirm and save meal"
            onSubmit={onConfirm}
            serverError={saveError}
            isSubmitting={createMeal.isPending}
          />
          <Button type="button" variant="ghost" onClick={() => setAnalysis(null)}>
            Discard analysis
          </Button>
        </div>
      )}
    </section>
  );
}

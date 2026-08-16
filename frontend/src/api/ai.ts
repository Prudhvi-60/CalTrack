import { apiClient } from "./client";
import type { AiCorrectionItem, AnalysisType, FoodAnalysis } from "@/types/ai";

export async function analyzeFoodImage(file: File, analysisType: AnalysisType): Promise<FoodAnalysis> {
  const form = new FormData();
  form.append("file", file);
  form.append("analysis_type", analysisType);
  const { data } = await apiClient.post<FoodAnalysis>("/api/v1/ai/analyze-food", form, {
    timeout: 60000,
  });
  return data;
}

export async function recordAiCorrections(
  analysisType: AnalysisType,
  items: AiCorrectionItem[],
  analysisId?: string | null,
): Promise<void> {
  if (items.length === 0) {
    return;
  }
  await apiClient.post("/api/v1/ai/corrections", {
    analysis_type: analysisType,
    analysis_id: analysisId ?? undefined,
    items,
  });
}

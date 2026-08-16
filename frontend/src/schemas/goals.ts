import { z } from "zod";

const nonNegative = z.coerce
  .number({ invalid_type_error: "Enter a number" })
  .refine((value) => Number.isFinite(value), "Enter a number")
  .refine((value) => value >= 0, "Must be 0 or greater");

export const goalSchema = z.object({
  daily_calorie_target: nonNegative,
  protein_target: nonNegative,
  carb_target: nonNegative,
  fat_target: nonNegative,
  weight_goal: z.preprocess(
    (value) => (value === "" || value === null || value === undefined ? null : value),
    z.union([nonNegative, z.null()]),
  ),
});

export type GoalFormValues = z.infer<typeof goalSchema>;

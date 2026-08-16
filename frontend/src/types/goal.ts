export type Goal = {
  id: number;
  user_id: number;
  daily_calorie_target: number;
  protein_target: number;
  carb_target: number;
  fat_target: number;
  weight_goal: number | null;
  calories_actual: number;
  protein_actual: number;
  carb_actual: number;
  fat_actual: number;
  calories_remaining: number;
  protein_remaining: number;
  carb_remaining: number;
  fat_remaining: number;
  progress_date: string;
  created_at: string;
  updated_at: string;
};

export type GoalPayload = {
  daily_calorie_target: number;
  protein_target: number;
  carb_target: number;
  fat_target: number;
  weight_goal: number | null;
};

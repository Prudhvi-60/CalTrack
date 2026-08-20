import { z } from "zod";

export const loginSchema = z.object({
  email: z.string().email("Enter a valid email"),
  password: z.string().min(1, "Password is required"),
});

export const registerSchema = z.object({
  display_name: z.string().trim().min(1, "Display name is required").max(120, "Name is too long"),
  username: z
    .string()
    .trim()
    .toLowerCase()
    .regex(/^[a-z][a-z0-9_]{2,23}$/, "Start with a letter; use 3–24 letters, numbers, or underscores"),
  email: z.string().email("Enter a valid email"),
  password: z.string().min(8, "Password must be at least 8 characters").max(72, "Password is too long"),
});

export const profileSchema = z.object({
  display_name: z.string().trim().min(1, "Display name is required").max(120, "Name is too long"),
  bio: z.string().max(500, "Bio is too long").optional(),
});

export const passwordSchema = z.object({
  current_password: z.string().min(1, "Current password is required"),
  new_password: z.string().min(8, "Password must be at least 8 characters").max(72, "Password is too long"),
});

export type LoginValues = z.infer<typeof loginSchema>;
export type RegisterValues = z.infer<typeof registerSchema>;
export type ProfileValues = z.infer<typeof profileSchema>;
export type PasswordValues = z.infer<typeof passwordSchema>;

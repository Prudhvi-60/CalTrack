/** CalTrack wellness palette — use for charts and non-Tailwind styles. */
export const palette = {
  forest: "#245C4A",
  sage: "#8FB5A5",
  terracotta: "#C98268",
  gold: "#D7B56D",
  background: "#F7F5F0",
  surface: "#FFFFFF",
  surfaceMuted: "#EEF4F0",
  text: "#24332D",
  muted: "#68766F",
  border: "#DCE4DF",
  error: "#B85C5C",
  success: "#4F8A6A",
  progressTrack: "#E5EBE7",
  navActive: "#E5F0EB",
} as const;

export const chartColors = {
  calories: palette.terracotta,
  protein: palette.sage,
  carbs: palette.gold,
  fat: palette.forest,
  fiber: palette.sage,
  primary: palette.forest,
  secondary: palette.sage,
  target: palette.sage,
} as const;

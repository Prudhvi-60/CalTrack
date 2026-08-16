import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { GuestRoute, ProtectedRoute } from "@/components/layout/ProtectedRoute";
import { Login } from "@/pages/Login";
import { Register } from "@/pages/Register";
import { Dashboard } from "@/pages/Dashboard";
import { Meals } from "@/pages/Meals";
import { NewMeal } from "@/pages/NewMeal";
import { MealDetails } from "@/pages/MealDetails";
import { MealEdit } from "@/pages/MealEdit";
import { Goals } from "@/pages/Goals";
import { Reports } from "@/pages/Reports";
import { AIScanner } from "@/pages/AIScanner";
import { Chat } from "@/pages/Chat";
import { PdfImport } from "@/pages/PdfImport";
import { Settings } from "@/pages/Settings";
import { NotFound } from "@/pages/NotFound";

export default function App() {
  return (
    <Routes>
      <Route element={<GuestRoute />}>
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
      </Route>
      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/meals" element={<Meals />} />
          <Route path="/meals/new" element={<NewMeal />} />
          <Route path="/meals/:mealId/edit" element={<MealEdit />} />
          <Route path="/meals/:mealId" element={<MealDetails />} />
          <Route path="/goals" element={<Goals />} />
          <Route path="/reports" element={<Reports />} />
          <Route path="/ai-scan" element={<AIScanner />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/import" element={<PdfImport />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="*" element={<NotFound />} />
        </Route>
      </Route>
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}

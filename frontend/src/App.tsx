import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppLayout } from "@/components/layout/AppLayout";
import { GuestRoute, ProtectedRoute } from "@/components/layout/ProtectedRoute";

const Login = lazy(() => import("@/pages/Login").then((module) => ({ default: module.Login })));
const Register = lazy(() => import("@/pages/Register").then((module) => ({ default: module.Register })));
const Dashboard = lazy(() => import("@/pages/Dashboard").then((module) => ({ default: module.Dashboard })));
const Meals = lazy(() => import("@/pages/Meals").then((module) => ({ default: module.Meals })));
const NewMeal = lazy(() => import("@/pages/NewMeal").then((module) => ({ default: module.NewMeal })));
const MealDetails = lazy(() => import("@/pages/MealDetails").then((module) => ({ default: module.MealDetails })));
const MealEdit = lazy(() => import("@/pages/MealEdit").then((module) => ({ default: module.MealEdit })));
const Goals = lazy(() => import("@/pages/Goals").then((module) => ({ default: module.Goals })));
const Reports = lazy(() => import("@/pages/Reports").then((module) => ({ default: module.Reports })));
const AIScanner = lazy(() => import("@/pages/AIScanner").then((module) => ({ default: module.AIScanner })));
const Chat = lazy(() => import("@/pages/Chat").then((module) => ({ default: module.Chat })));
const PdfImport = lazy(() => import("@/pages/PdfImport").then((module) => ({ default: module.PdfImport })));
const Settings = lazy(() => import("@/pages/Settings").then((module) => ({ default: module.Settings })));
const NotFound = lazy(() => import("@/pages/NotFound").then((module) => ({ default: module.NotFound })));

export default function App() {
  return (
    <Suspense
      fallback={
        <div className="grid min-h-screen place-items-center text-sm text-muted-foreground" role="status">
          Loading page…
        </div>
      }
    >
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
    </Suspense>
  );
}

import { Link, useLocation, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field } from "@/components/ui/field";
import { ErrorAlert } from "@/components/ui/error-alert";
import { AuthShell } from "@/layouts/AuthShell";
import { useAuth } from "@/contexts/AuthContext";
import { loginSchema, type LoginValues } from "@/features/auth/schemas";
import { getApiErrorMessage } from "@/api/auth";

export function LoginPage() {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/";
  const [serverError, setServerError] = useState<string | null>(null);

  const form = useForm<LoginValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { email: "", password: "" },
  });

  async function onSubmit(values: LoginValues) {
    setServerError(null);
    try {
      await login(values);
      navigate(from, { replace: true });
    } catch (error) {
      setServerError(getApiErrorMessage(error, "Could not sign in"));
    }
  }

  return (
    <AuthShell
      title="Welcome back"
      description="Sign in to keep your shelves, lists, and reviews."
      footer={
        <>
          New here?{" "}
          <Link className="text-wine underline-offset-4 hover:underline" to="/register">
            Create an account
          </Link>
        </>
      }
    >
      <form className="mt-6 space-y-4" onSubmit={form.handleSubmit(onSubmit)} noValidate>
        <Field label="Email" id="email" error={form.formState.errors.email?.message}>
          <Input id="email" type="email" autoComplete="email" {...form.register("email")} />
        </Field>
        <Field label="Password" id="password" error={form.formState.errors.password?.message}>
          <Input id="password" type="password" autoComplete="current-password" {...form.register("password")} />
        </Field>
        {serverError ? <ErrorAlert message={serverError} /> : null}
        <Button className="w-full" type="submit" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? "Signing in…" : "Sign in"}
        </Button>
      </form>
    </AuthShell>
  );
}

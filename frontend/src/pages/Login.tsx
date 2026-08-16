import { Link, useLocation, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field } from "@/components/ui/field";
import { ErrorAlert } from "@/components/ui/error-alert";
import { AuthShell } from "@/components/layout/AuthShell";
import { useAuth } from "@/contexts/AuthContext";
import { loginSchema, type LoginValues } from "@/schemas/auth";
import { getApiErrorMessage } from "@/api/auth";
import { usePageTitle } from "@/hooks/usePageTitle";

export function Login() {
  usePageTitle("Sign in");
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const from = (location.state as { from?: string } | null)?.from ?? "/dashboard";
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
      title="Sign in to CalTrack"
      description="Use your account to track meals and goals."
      footer={
        <>
          Need an account?{" "}
          <Link className="text-primary underline" to="/register">
            Register
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
        {serverError && <ErrorAlert message={serverError} />}
        <Button className="w-full" type="submit" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? "Signing in…" : "Sign in"}
        </Button>
      </form>
    </AuthShell>
  );
}

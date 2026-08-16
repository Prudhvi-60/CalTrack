import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field } from "@/components/ui/field";
import { ErrorAlert } from "@/components/ui/error-alert";
import { AuthShell } from "@/components/layout/AuthShell";
import { useAuth } from "@/contexts/AuthContext";
import { registerSchema, type RegisterValues } from "@/schemas/auth";
import { getApiErrorMessage } from "@/api/auth";
import { usePageTitle } from "@/hooks/usePageTitle";

export function Register() {
  usePageTitle("Register");
  const { register: registerAccount } = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);

  const form = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { name: "", email: "", password: "" },
  });

  async function onSubmit(values: RegisterValues) {
    setServerError(null);
    try {
      await registerAccount(values);
      navigate("/dashboard", { replace: true });
    } catch (error) {
      setServerError(getApiErrorMessage(error, "Could not create account"));
    }
  }

  return (
    <AuthShell
      title="Create your CalTrack account"
      description="Your meals and goals stay private to this account."
      footer={
        <>
          Already registered?{" "}
          <Link className="text-primary underline" to="/login">
            Sign in
          </Link>
        </>
      }
    >
      <form className="mt-6 space-y-4" onSubmit={form.handleSubmit(onSubmit)} noValidate>
        <Field label="Name" id="name" error={form.formState.errors.name?.message}>
          <Input id="name" autoComplete="name" {...form.register("name")} />
        </Field>
        <Field label="Email" id="email" error={form.formState.errors.email?.message}>
          <Input id="email" type="email" autoComplete="email" {...form.register("email")} />
        </Field>
        <Field label="Password" id="password" error={form.formState.errors.password?.message}>
          <Input id="password" type="password" autoComplete="new-password" {...form.register("password")} />
        </Field>
        {serverError && <ErrorAlert message={serverError} />}
        <Button className="w-full" type="submit" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? "Creating account…" : "Create account"}
        </Button>
      </form>
    </AuthShell>
  );
}

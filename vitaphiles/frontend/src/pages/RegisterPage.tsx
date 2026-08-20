import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field } from "@/components/ui/field";
import { ErrorAlert } from "@/components/ui/error-alert";
import { AuthShell } from "@/layouts/AuthShell";
import { useAuth } from "@/contexts/AuthContext";
import { registerSchema, type RegisterValues } from "@/features/auth/schemas";
import { getApiErrorMessage } from "@/api/auth";

export function RegisterPage() {
  const { register: registerAccount } = useAuth();
  const navigate = useNavigate();
  const [serverError, setServerError] = useState<string | null>(null);

  const form = useForm<RegisterValues>({
    resolver: zodResolver(registerSchema),
    defaultValues: { display_name: "", username: "", email: "", password: "" },
  });

  async function onSubmit(values: RegisterValues) {
    setServerError(null);
    try {
      await registerAccount(values);
      navigate("/", { replace: true });
    } catch (error) {
      setServerError(getApiErrorMessage(error, "Could not create account"));
    }
  }

  return (
    <AuthShell
      title="Join the archive"
      description="A private shelf for the books and films that stay with you."
      footer={
        <>
          Already a member?{" "}
          <Link className="text-wine underline-offset-4 hover:underline" to="/login">
            Sign in
          </Link>
        </>
      }
    >
      <form className="mt-6 space-y-4" onSubmit={form.handleSubmit(onSubmit)} noValidate>
        <Field label="Display name" id="display_name" error={form.formState.errors.display_name?.message}>
          <Input id="display_name" autoComplete="name" {...form.register("display_name")} />
        </Field>
        <Field
          label="Username"
          id="username"
          hint="Public handle, like prudhvi"
          error={form.formState.errors.username?.message}
        >
          <Input id="username" autoComplete="username" {...form.register("username")} />
        </Field>
        <Field label="Email" id="email" error={form.formState.errors.email?.message}>
          <Input id="email" type="email" autoComplete="email" {...form.register("email")} />
        </Field>
        <Field label="Password" id="password" error={form.formState.errors.password?.message}>
          <Input id="password" type="password" autoComplete="new-password" {...form.register("password")} />
        </Field>
        {serverError ? <ErrorAlert message={serverError} /> : null}
        <Button className="w-full" type="submit" disabled={form.formState.isSubmitting}>
          {form.formState.isSubmitting ? "Creating account…" : "Create account"}
        </Button>
      </form>
    </AuthShell>
  );
}

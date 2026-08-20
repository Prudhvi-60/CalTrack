import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field } from "@/components/ui/field";
import { ErrorAlert } from "@/components/ui/error-alert";
import { useAuth } from "@/contexts/AuthContext";
import { passwordSchema, profileSchema, type PasswordValues, type ProfileValues } from "@/features/auth/schemas";
import { getApiErrorMessage } from "@/api/auth";

export function ProfilePage() {
  const { user, saveProfile, savePassword, logout } = useAuth();
  const [profileError, setProfileError] = useState<string | null>(null);
  const [profileOk, setProfileOk] = useState(false);
  const [passwordError, setPasswordError] = useState<string | null>(null);

  const profileForm = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema),
    values: { display_name: user?.display_name ?? "", bio: user?.bio ?? "" },
  });

  const passwordForm = useForm<PasswordValues>({
    resolver: zodResolver(passwordSchema),
    defaultValues: { current_password: "", new_password: "" },
  });

  if (!user) {
    return null;
  }

  async function onProfile(values: ProfileValues) {
    setProfileError(null);
    setProfileOk(false);
    try {
      await saveProfile({ display_name: values.display_name, bio: values.bio ?? "" });
      setProfileOk(true);
    } catch (error) {
      setProfileError(getApiErrorMessage(error, "Could not update profile"));
    }
  }

  async function onPassword(values: PasswordValues) {
    setPasswordError(null);
    try {
      await savePassword(values.current_password, values.new_password);
    } catch (error) {
      setPasswordError(getApiErrorMessage(error, "Could not change password"));
    }
  }

  return (
    <div className="space-y-10">
      <header>
        <p className="font-display text-3xl italic text-ink/50">@{user.username}</p>
        <h1 className="mt-1 font-display text-5xl">{user.display_name}</h1>
        <p className="mt-3 text-sm text-ink/55">{user.email}</p>
      </header>

      <section className="max-w-lg space-y-4 border border-ink/10 bg-ivory p-6">
        <h2 className="font-display text-2xl">Profile</h2>
        <form className="space-y-4" onSubmit={profileForm.handleSubmit(onProfile)} noValidate>
          <Field label="Display name" id="display_name" error={profileForm.formState.errors.display_name?.message}>
            <Input {...profileForm.register("display_name")} />
          </Field>
          <Field label="Bio" id="bio" error={profileForm.formState.errors.bio?.message}>
            <Input {...profileForm.register("bio")} />
          </Field>
          {profileError ? <ErrorAlert message={profileError} /> : null}
          {profileOk ? <p className="text-sm text-ink/60">Saved.</p> : null}
          <Button type="submit" disabled={profileForm.formState.isSubmitting}>
            {profileForm.formState.isSubmitting ? "Saving…" : "Save profile"}
          </Button>
        </form>
      </section>

      <section className="max-w-lg space-y-4 border border-ink/10 bg-ivory p-6">
        <h2 className="font-display text-2xl">Password</h2>
        <p className="text-sm text-ink/55">Changing your password signs you out of other sessions.</p>
        <form className="space-y-4" onSubmit={passwordForm.handleSubmit(onPassword)} noValidate>
          <Field
            label="Current password"
            id="current_password"
            error={passwordForm.formState.errors.current_password?.message}
          >
            <Input type="password" autoComplete="current-password" {...passwordForm.register("current_password")} />
          </Field>
          <Field label="New password" id="new_password" error={passwordForm.formState.errors.new_password?.message}>
            <Input type="password" autoComplete="new-password" {...passwordForm.register("new_password")} />
          </Field>
          {passwordError ? <ErrorAlert message={passwordError} /> : null}
          <Button type="submit" disabled={passwordForm.formState.isSubmitting}>
            {passwordForm.formState.isSubmitting ? "Updating…" : "Update password"}
          </Button>
        </form>
      </section>

      <Button type="button" variant="outline" onClick={() => void logout()}>
        Sign out
      </Button>
    </div>
  );
}

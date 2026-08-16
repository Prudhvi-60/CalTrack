import { useState } from "react";
import { useForm, type Resolver } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useAuth } from "@/contexts/AuthContext";
import { changePassword, getApiErrorMessage } from "@/api/auth";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Field } from "@/components/ui/field";
import { ErrorAlert } from "@/components/ui/error-alert";
import { PageHeader } from "@/components/ui/page-header";
import { usePageTitle } from "@/hooks/usePageTitle";
import { passwordSchema, profileSchema, type PasswordValues, type ProfileValues } from "@/schemas/auth";

export function Settings() {
  usePageTitle("Settings");
  const { user, logout, setUserName, updateUser } = useAuth();
  const [trainingError, setTrainingError] = useState<string | null>(null);
  const [trainingSaved, setTrainingSaved] = useState(false);
  const [trainingBusy, setTrainingBusy] = useState(false);
  const [profileError, setProfileError] = useState<string | null>(null);
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [profileSaved, setProfileSaved] = useState(false);
  const [passwordSaved, setPasswordSaved] = useState(false);

  const profileForm = useForm<ProfileValues>({
    resolver: zodResolver(profileSchema) as Resolver<ProfileValues>,
    defaultValues: { name: user?.name ?? "" },
    values: { name: user?.name ?? "" },
  });
  const passwordForm = useForm<PasswordValues>({
    resolver: zodResolver(passwordSchema) as Resolver<PasswordValues>,
    defaultValues: { current_password: "", new_password: "" },
  });

  async function onProfile(values: ProfileValues) {
    setProfileError(null);
    setProfileSaved(false);
    try {
      await setUserName(values.name);
      setProfileSaved(true);
    } catch (error) {
      setProfileError(getApiErrorMessage(error, "Could not update profile"));
    }
  }

  async function onPassword(values: PasswordValues) {
    setPasswordError(null);
    setPasswordSaved(false);
    try {
      await changePassword(values.current_password, values.new_password);
      passwordForm.reset({ current_password: "", new_password: "" });
      setPasswordSaved(true);
    } catch (error) {
      setPasswordError(getApiErrorMessage(error, "Could not change password"));
    }
  }

  return (
    <section className="space-y-6">
      <PageHeader title="Settings" description="Account details stay private to this login." />
      <div className="rounded-lg border bg-card p-6">
        <p className="text-sm text-muted-foreground">Email</p>
        <p className="font-medium">{user?.email}</p>
      </div>
      <form className="max-w-xl space-y-4 rounded-lg border bg-card p-6" onSubmit={profileForm.handleSubmit(onProfile)} noValidate>
        <h2 className="text-lg font-medium">Display name</h2>
        <Field label="Name" id="name" error={profileForm.formState.errors.name?.message}>
          <Input id="name" {...profileForm.register("name")} />
        </Field>
        {profileError && <ErrorAlert message={profileError} />}
        {profileSaved && <p className="text-sm text-muted-foreground">Name saved.</p>}
        <Button type="submit" disabled={profileForm.formState.isSubmitting}>
          {profileForm.formState.isSubmitting ? "Saving…" : "Save name"}
        </Button>
      </form>
      <form className="max-w-xl space-y-4 rounded-lg border bg-card p-6" onSubmit={passwordForm.handleSubmit(onPassword)} noValidate>
        <h2 className="text-lg font-medium">Password</h2>
        <Field label="Current password" id="current_password" error={passwordForm.formState.errors.current_password?.message}>
          <Input id="current_password" type="password" autoComplete="current-password" {...passwordForm.register("current_password")} />
        </Field>
        <Field label="New password" id="new_password" error={passwordForm.formState.errors.new_password?.message}>
          <Input id="new_password" type="password" autoComplete="new-password" {...passwordForm.register("new_password")} />
        </Field>
        {passwordError && <ErrorAlert message={passwordError} />}
        {passwordSaved && <p className="text-sm text-muted-foreground">Password updated.</p>}
        <Button type="submit" disabled={passwordForm.formState.isSubmitting}>
          {passwordForm.formState.isSubmitting ? "Updating…" : "Change password"}
        </Button>
      </form>
      <div className="max-w-xl space-y-3 rounded-lg border bg-card p-6">
        <h2 className="text-lg font-medium">Training data</h2>
        <p className="text-sm text-muted-foreground">
          Off by default. If you opt in, CalTrack may store a copy of scanner images you submit together with
          your food and portion corrections, so a future food classifier can be evaluated. Images are stored
          under generated names. You can turn this off at any time. Unedited predictions are recorded as
          confirmations, not assumed-correct training labels.
        </p>
        <label className="flex items-start gap-3 text-sm">
          <input
            type="checkbox"
            className="mt-1"
            checked={Boolean(user?.allow_training_data_collection)}
            disabled={trainingBusy}
            onChange={(event) => {
              setTrainingError(null);
              setTrainingSaved(false);
              setTrainingBusy(true);
              void updateUser({ allow_training_data_collection: event.target.checked })
                .then(() => setTrainingSaved(true))
                .catch((error) => setTrainingError(getApiErrorMessage(error, "Could not update training preference")))
                .finally(() => setTrainingBusy(false));
            }}
          />
          <span>Allow my opted-in scanner images and corrections to be used for model improvement</span>
        </label>
        {trainingError && <ErrorAlert message={trainingError} />}
        {trainingSaved && <p className="text-sm text-muted-foreground">Training preference saved.</p>}
      </div>
      <Button variant="secondary" type="button" onClick={() => void logout()}>
        Sign out
      </Button>
    </section>
  );
}

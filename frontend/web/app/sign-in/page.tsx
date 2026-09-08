"use client";

import Link from "next/link";
import { useState } from "react";

import { Field } from "@/components/ui/Field";
import { NotWiredError, signIn } from "@/lib/api/authApi";

/**
 * Supplier sign in.
 *
 * THERE IS NO BUSINESS SIGN IN HERE, and that is not an omission. A
 * business has no web surface (V2_00 section 2.9) -- if one arrives on
 * this page they have taken a wrong turn, so the page says so plainly at
 * the bottom rather than letting them try credentials that will never
 * work.
 */
export default function SignInPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);

    const next: Record<string, string> = {};
    if (!email.trim()) next.email = "Enter your email address.";
    if (!password) next.password = "Enter your password.";
    setErrors(next);
    if (Object.keys(next).length > 0) return;

    setBusy(true);
    try {
      await signIn({ email: email.trim(), password });
    } catch (error) {
      setFormError(
        error instanceof NotWiredError
          ? error.message
          : "Something went wrong. Please try again.",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="mx-auto max-w-md px-5 py-16 sm:py-24">
      <h1 className="text-3xl font-bold tracking-tight text-brand-blue">
        Supplier sign in
      </h1>
      <p className="mt-3 text-ink-muted">
        Manage your catalogue, terms and profile.
      </p>

      <form onSubmit={handleSubmit} noValidate className="mt-10 space-y-5">
        <Field
          id="email"
          label="Email address"
          type="email"
          inputMode="email"
          autoComplete="email"
          value={email}
          onChange={setEmail}
          error={errors.email}
          required
        />
        <Field
          id="password"
          label="Password"
          type="password"
          autoComplete="current-password"
          value={password}
          onChange={setPassword}
          error={errors.password}
          required
        />

        {formError && (
          <div
            role="alert"
            className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900"
          >
            {formError}
          </div>
        )}

        <button
          type="submit"
          disabled={busy}
          className="w-full rounded-lg bg-brand-blue px-6 py-3.5 text-base font-semibold text-white transition-colors hover:bg-brand-blue-light disabled:opacity-60 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-blue"
        >
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <p className="mt-8 text-sm text-ink-muted">
        Do not have an account?{" "}
        <Link
          href="/sign-up"
          className="font-semibold text-brand-blue hover:text-brand-green"
        >
          Create a supplier account
        </Link>
      </p>

      <p className="mt-6 border-t border-line/60 pt-6 text-sm text-ink-muted">
        Buying stock for your business? TruConnect for businesses is in the app
        — there is nothing to sign in to here.
      </p>
    </div>
  );
}

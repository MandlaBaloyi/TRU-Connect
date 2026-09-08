"use client";

import Link from "next/link";
import { useState } from "react";

import { Field } from "@/design-system/primitives/Field";
import { SocialSignIn } from "@/domains/auth/components/SocialSignIn";
import { NotWiredError, signIn } from "@/domains/auth/services/authApi";
import { routes } from "@/config/routes";

/**
 * Supplier sign in.
 *
 * DELIBERATELY THE SAME SHAPE AS SIGN-UP -- same heading scale, same
 * social block, same field styling, same footer link. They were
 * noticeably different before, and two pages a supplier moves between in
 * one session looking like two different products is the cheapest
 * possible way to seem unfinished.
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
    <>
      <h1 className="text-3xl font-bold tracking-tight text-brand-blue">Welcome back</h1>
      <p className="mt-2 text-ink-muted">Sign in to manage your catalogue and orders.</p>

      <div className="mt-8">
        <SocialSignIn action="sign in" />
      </div>

      <form onSubmit={handleSubmit} noValidate className="space-y-5">
        <Field
          id="email"
          label="Email address"
          type="email"
          inputMode="email"
          autoComplete="email"
          placeholder="you@yourbusiness.co.za"
          value={email}
          onChange={setEmail}
          error={errors.email}
          required
          autoFocus
        />

        <div>
          <Field
            id="password"
            label="Password"
            type="password"
            autoComplete="current-password"
            placeholder="Your password"
            value={password}
            onChange={setPassword}
            error={errors.password}
            required
          />
          {/* Under the field it belongs to, not floating beside the
              label -- someone reaches for this AFTER a password has
              failed them, which is exactly where their eye already is. */}
          <div className="mt-2 text-right">
            <Link
              href={routes.contact}
              className="text-sm font-medium text-brand-blue hover:text-brand-green"
            >
              Forgot your password?
            </Link>
          </div>
        </div>

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
          className="w-full rounded-lg bg-brand-blue px-6 py-3.5 text-base font-semibold text-white shadow-sm transition-colors hover:bg-brand-blue-light disabled:opacity-60 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-blue"
        >
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>

      <p className="mt-8 text-center text-sm text-ink-muted">
        New to TruConnect?{" "}
        <Link href={routes.signUp} className="font-semibold text-brand-blue hover:text-brand-green">
          Create a supplier account
        </Link>
      </p>
    </>
  );
}

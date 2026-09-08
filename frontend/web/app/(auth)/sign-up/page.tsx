"use client";

import Link from "next/link";
import { useState } from "react";

import { Field } from "@/design-system/primitives/Field";
import { SocialSignIn } from "@/domains/auth/components/SocialSignIn";
import { NotWiredError, signUpSupplier } from "@/domains/auth/services/authApi";
import { routes } from "@/config/routes";

/**
 * Supplier sign up.
 *
 * BUSINESS NAME IS REQUIRED; OWNER NAME IS NOT. The business name is
 * what every business-facing screen shows, so it has to be real. The
 * owner's own name is theirs and is nobody's business -- in v1 the
 * profile was seeded from the OWNER name because the business name was
 * collected and then never persisted, which is how suppliers ended up
 * listed under a person's name.
 *
 * THE NAME RULES MIRROR THE BACKEND deliberately (2-50 characters, at
 * least one letter, not a single repeated character). The same
 * hand-kept-in-sync discipline as row_validator.py and its TypeScript
 * counterpart: two copies, because the alternative is a shared package
 * carrying four lines of regex.
 *
 * NO PAGE CONTAINER OF ITS OWN. This used to wrap itself in
 * `mx-auto max-w-md px-5 py-16`, which the auth layout was ALREADY
 * providing -- so sign-up sat at a different width and vertical offset
 * from sign-in, and moving between the two pages looked like the header
 * shifted. The shell owns the frame; a page inside it renders content.
 *
 * FIVE FIELDS ARE GROUPED, not stacked flat. "About your business" then
 * "Your login" is two short decisions instead of one long one, and it
 * puts the optional field in the group where skipping it is obviously
 * fine.
 */

const HAS_LETTER = /[^\W\d_]/u;

function validateBusinessName(raw: string): string | undefined {
  const value = raw.trim().replace(/\s+/g, " ");
  if (!value) return "Enter your business name.";
  if (value.length < 2) return "Business name is too short.";
  if (value.length > 50) return "Business name must be 50 characters or fewer.";
  if (!HAS_LETTER.test(value))
    return "Business name must contain at least one letter.";
  if (new Set(value.replace(/ /g, "")).size <= 1)
    return "Enter your real business name.";
  return undefined;
}

function GroupLabel({ children }: { children: React.ReactNode }) {
  return (
    <p className="text-xs font-semibold uppercase tracking-wider text-ink-muted">{children}</p>
  );
}

export default function SignUpPage() {
  const [businessName, setBusinessName] = useState("");
  const [ownerName, setOwnerName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);

    const next: Record<string, string> = {};
    const nameError = validateBusinessName(businessName);
    if (nameError) next.businessName = nameError;
    if (!email.trim()) next.email = "Enter your email address.";
    if (!phone.trim()) next.phone = "Enter a contact number.";
    if (password.length < 8) next.password = "Use at least 8 characters.";
    setErrors(next);
    if (Object.keys(next).length > 0) return;

    setBusy(true);
    try {
      await signUpSupplier({
        businessName: businessName.trim().replace(/\s+/g, " "),
        ownerName: ownerName.trim() || undefined,
        email: email.trim(),
        phone: phone.trim(),
        password,
      });
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
      <h1 className="text-3xl font-bold tracking-tight text-brand-blue">
        Create a supplier account
      </h1>
      <p className="mt-2 text-ink-muted">
        Nothing goes live until you say so. You choose what businesses can see.
      </p>

      <div className="mt-8">
        <SocialSignIn action="sign up" />
      </div>

      <form onSubmit={handleSubmit} noValidate className="space-y-8">
        <div className="space-y-5">
          <GroupLabel>About your business</GroupLabel>
          <Field
            id="businessName"
            label="Business name"
            hint="Businesses see this"
            autoComplete="organization"
            placeholder="e.g. MacMan Wholesalers"
            value={businessName}
            onChange={setBusinessName}
            error={errors.businessName}
            required
            autoFocus
          />
          <Field
            id="ownerName"
            label="Your name"
            autoComplete="name"
            placeholder="Who we should ask for"
            value={ownerName}
            onChange={setOwnerName}
            error={errors.ownerName}
          />
        </div>

        <div className="space-y-5">
          <GroupLabel>Your login</GroupLabel>
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
          />
          <Field
            id="phone"
            label="Contact number"
            type="tel"
            inputMode="tel"
            autoComplete="tel"
            placeholder="082 123 4567"
            value={phone}
            onChange={setPhone}
            error={errors.phone}
            required
          />
          <Field
            id="password"
            label="Password"
            type="password"
            hint="8 characters or more"
            autoComplete="new-password"
            placeholder="Choose a password"
            value={password}
            onChange={setPassword}
            error={errors.password}
            required
          />
        </div>

        {formError && (
          <div
            role="alert"
            className="rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900"
          >
            {formError}
          </div>
        )}

        <div className="space-y-4">
          <button
            type="submit"
            disabled={busy}
            className="w-full rounded-lg bg-brand-blue px-6 py-3.5 text-base font-semibold text-white shadow-sm transition-colors hover:bg-brand-blue-light disabled:opacity-60 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-blue"
          >
            {busy ? "Creating account…" : "Create account"}
          </button>

          {/* Under the button, not above it. Someone reads this at the
              moment they commit, and putting it here does not push the
              button further down a form that is already five fields. */}
          <p className="text-center text-xs leading-relaxed text-ink-muted">
            By creating an account you agree to our{" "}
            <Link href={routes.terms} className="underline hover:text-ink">
              Terms
            </Link>{" "}
            and{" "}
            <Link href={routes.privacy} className="underline hover:text-ink">
              Privacy Policy
            </Link>
            .
          </p>
        </div>
      </form>

      <p className="mt-8 text-center text-sm text-ink-muted">
        Already have an account?{" "}
        <Link href={routes.signIn} className="font-semibold text-brand-blue hover:text-brand-green">
          Sign in
        </Link>
      </p>
    </>
  );
}

"use client";

import Link from "next/link";
import { useState } from "react";

import { Field } from "@/design-system/primitives/Field";
import { SocialSignIn } from "@/domains/auth/components/SocialSignIn";
import { ApiError, signUpSupplier } from "@/domains/auth/services/authApi";
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
 * THE VALIDATION MIRRORS THE BACKEND deliberately, field for field: the
 * business-name rule (2-50 characters, at least one letter, not a
 * single repeated character) matches shared/validation/business_name.py,
 * and the password rule matches validate_password_complexity in
 * shared/security/security.py. Two copies, hand-kept in sync, the same
 * discipline as row_validator.py and its TypeScript counterpart -- the
 * alternative is a shared package carrying a dozen lines of regex.
 *
 * The point of duplicating them is not to replace the server check. It
 * is that being told "password needs a capital letter" as you type
 * beats being told it after a round trip.
 *
 * NO PHONE FIELD. It used to be here and had nowhere to go:
 * registration does not collect a number, because a phone is attached
 * later through the OTP flow where it is actually verified. A field
 * whose value is silently discarded is worse than no field.
 *
 * NO PAGE CONTAINER OF ITS OWN. This used to wrap itself in
 * `mx-auto max-w-md px-5 py-16`, which the auth layout was ALREADY
 * providing -- so sign-up sat at a different width and vertical offset
 * from sign-in, and moving between the two pages looked like the header
 * shifted. The shell owns the frame; a page inside it renders content.
 */

const HAS_LETTER = /[^\W\d_]/u;
const SPECIAL_CHARACTERS = /[@$!%*?&.#^()_\-+=]/;

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

function validatePassword(value: string): string | undefined {
  if (value.length < 8) return "Use at least 8 characters.";
  if (!/[a-z]/.test(value)) return "Include a lowercase letter.";
  if (!/[A-Z]/.test(value)) return "Include a capital letter.";
  if (!/\d/.test(value)) return "Include a number.";
  if (!SPECIAL_CHARACTERS.test(value))
    return "Include a special character, like ! or @.";
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
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [acceptTerms, setAcceptTerms] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [formError, setFormError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [done, setDone] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setFormError(null);

    const next: Record<string, string> = {};
    const nameError = validateBusinessName(businessName);
    if (nameError) next.businessName = nameError;
    if (!email.trim()) next.email = "Enter your email address.";

    const passwordError = validatePassword(password);
    if (passwordError) next.password = passwordError;
    if (confirmPassword !== password)
      next.confirmPassword = "Passwords do not match.";
    if (!acceptTerms) next.acceptTerms = "Please accept the terms to continue.";

    setErrors(next);
    if (Object.keys(next).length > 0) return;

    setBusy(true);
    try {
      await signUpSupplier({
        businessName: businessName.trim().replace(/\s+/g, " "),
        ownerName: ownerName.trim() || undefined,
        email: email.trim(),
        password,
        confirmPassword,
        acceptTerms,
      });
      setDone(true);
    } catch (error) {
      setFormError(
        error instanceof ApiError
          ? error.message
          : "Something went wrong. Please try again.",
      );
    } finally {
      setBusy(false);
    }
  }

  // REGISTRATION ISSUES NO SESSION, on purpose -- there is no valid
  // session for an unverified account, so there is nowhere to redirect
  // to. This screen is the honest end of the flow: the next step
  // genuinely happens in their inbox.
  if (done) {
    return (
      <>
        <h1 className="text-3xl font-bold tracking-tight text-brand-blue">Check your email</h1>
        <p className="mt-3 leading-relaxed text-ink-muted">
          We sent a verification code to <strong className="text-ink">{email.trim()}</strong>.
          Enter it to finish setting up {businessName.trim()}.
        </p>
        <p className="mt-6 text-sm leading-relaxed text-ink-muted">
          Nothing is visible to businesses yet. Your shopfront stays closed until you open it.
        </p>
        <p className="mt-8 text-sm text-ink-muted">
          Already verified?{" "}
          <Link
            href={routes.signIn}
            className="font-semibold text-brand-blue hover:text-brand-green"
          >
            Sign in
          </Link>
        </p>
      </>
    );
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
            id="password"
            label="Password"
            type="password"
            hint="8+ with a capital, a number and a symbol"
            autoComplete="new-password"
            placeholder="Choose a password"
            value={password}
            onChange={setPassword}
            error={errors.password}
            required
          />
          <Field
            id="confirmPassword"
            label="Confirm password"
            type="password"
            autoComplete="new-password"
            placeholder="Type it again"
            value={confirmPassword}
            onChange={setConfirmPassword}
            error={errors.confirmPassword}
            required
          />
        </div>

        {/* AN EXPLICIT TICK, not a line of small print under the button.
            The backend requires acceptTerms and will reject the
            registration without it, so consent has to be a real action
            the person took rather than something we assert on their
            behalf. */}
        <div>
          <label className="flex cursor-pointer items-start gap-3">
            <input
              type="checkbox"
              checked={acceptTerms}
              onChange={(event) => setAcceptTerms(event.target.checked)}
              className="mt-0.5 h-5 w-5 shrink-0 rounded border-line text-brand-blue focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-blue"
              aria-invalid={errors.acceptTerms ? true : undefined}
              aria-describedby={errors.acceptTerms ? "acceptTerms-error" : undefined}
            />
            <span className="text-sm leading-relaxed text-ink-muted">
              I agree to the{" "}
              <Link href={routes.terms} className="font-medium text-brand-blue hover:underline">
                Terms
              </Link>{" "}
              and{" "}
              <Link href={routes.privacy} className="font-medium text-brand-blue hover:underline">
                Privacy Policy
              </Link>
              .
            </span>
          </label>
          {errors.acceptTerms && (
            <p id="acceptTerms-error" className="mt-1.5 text-sm text-red-600">
              {errors.acceptTerms}
            </p>
          )}
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
          {busy ? "Creating account…" : "Create account"}
        </button>
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

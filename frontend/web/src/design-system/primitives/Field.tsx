"use client";

import { useState } from "react";

/**
 * A labelled form input.
 *
 * LABEL, NOT PLACEHOLDER-AS-LABEL. A placeholder disappears the moment
 * someone types, which turns every review pass into guesswork and is
 * invisible to a screen reader. The label stays, and the placeholder is
 * used for what it is actually good at: showing the SHAPE of the answer
 * ("082 123 4567") so nobody has to guess the format.
 *
 * ERRORS ARE WIRED, NOT JUST COLOURED. aria-invalid and
 * aria-describedby, because red text alone tells a sighted user
 * something is wrong and tells everyone else nothing.
 *
 * THE PASSWORD REVEAL IS NOT A LUXURY HERE. This audience is typing a
 * password on a phone, often outdoors, frequently one-handed. Without a
 * reveal the only recovery from a typo is to clear the field and start
 * again, and that is a real reason people abandon a sign-up. It is a
 * button rather than a checkbox so it sits inside the field where the
 * thumb already is.
 *
 * "OPTIONAL" IS MARKED, "REQUIRED" IS NOT. Most fields are required, so
 * marking those adds an asterisk to almost every line and stops carrying
 * information. Marking the rare exception is the version that actually
 * tells you something.
 */
export function Field({
  id,
  label,
  type = "text",
  value,
  onChange,
  error,
  hint,
  placeholder,
  autoComplete,
  required,
  inputMode,
  autoFocus,
}: {
  id: string;
  label: string;
  type?: string;
  value: string;
  onChange: (next: string) => void;
  error?: string;
  hint?: string;
  placeholder?: string;
  autoComplete?: string;
  required?: boolean;
  inputMode?: "text" | "email" | "tel" | "numeric";
  autoFocus?: boolean;
}) {
  const [revealed, setRevealed] = useState(false);

  const isPassword = type === "password";
  const inputType = isPassword && revealed ? "text" : type;

  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div>
      <div className="flex items-baseline justify-between gap-3">
        <label htmlFor={id} className="text-sm font-semibold text-ink">
          {label}
          {!required && (
            <span className="ml-1.5 text-xs font-normal text-ink-muted">optional</span>
          )}
        </label>
        {hint && (
          <span id={hintId} className="text-xs text-ink-muted">
            {hint}
          </span>
        )}
      </div>

      <div className="relative mt-1.5">
        <input
          id={id}
          type={inputType}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          autoComplete={autoComplete}
          inputMode={inputMode}
          autoFocus={autoFocus}
          aria-invalid={error ? true : undefined}
          aria-describedby={describedBy}
          className={`w-full rounded-lg border bg-white px-3.5 py-3 text-base text-ink outline-none transition-shadow placeholder:text-ink-muted/60 focus:ring-4 ${
            isPassword ? "pr-20" : ""
          } ${
            error
              ? "border-red-500 focus:border-red-500 focus:ring-red-500/15"
              : "border-line focus:border-brand-blue focus:ring-brand-blue/15"
          }`}
        />

        {isPassword && (
          <button
            type="button"
            onClick={() => setRevealed((shown) => !shown)}
            className="absolute inset-y-0 right-0 flex items-center rounded-r-lg px-3.5 text-sm font-semibold text-ink-muted transition-colors hover:text-brand-blue focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-brand-blue"
            // The control's own name changes with its state, so a screen
            // reader announces what the next press will DO rather than
            // what is currently true.
            aria-label={revealed ? "Hide password" : "Show password"}
          >
            {revealed ? "Hide" : "Show"}
          </button>
        )}
      </div>

      {error && (
        <p id={errorId} className="mt-1.5 text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}

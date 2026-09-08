/**
 * A labelled form input.
 *
 * LABEL, NOT PLACEHOLDER-AS-LABEL. A placeholder disappears the moment
 * someone types, which turns every review pass into guesswork and is
 * invisible to a screen reader. The label stays.
 *
 * The error is wired with aria-describedby and aria-invalid rather than
 * just coloured red -- a supplier filling this in on a bad connection at
 * the back of a shop is exactly the person who needs it to be legible.
 */
export function Field({
  id,
  label,
  type = "text",
  value,
  onChange,
  error,
  hint,
  autoComplete,
  required,
  inputMode,
}: {
  id: string;
  label: string;
  type?: string;
  value: string;
  onChange: (next: string) => void;
  error?: string;
  hint?: string;
  autoComplete?: string;
  required?: boolean;
  inputMode?: "text" | "email" | "tel" | "numeric";
}) {
  const hintId = hint ? `${id}-hint` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [hintId, errorId].filter(Boolean).join(" ") || undefined;

  return (
    <div>
      <label htmlFor={id} className="block text-sm font-semibold text-ink">
        {label}
        {!required && (
          <span className="ml-1.5 font-normal text-ink-muted">(optional)</span>
        )}
      </label>

      {hint && (
        <p id={hintId} className="mt-1 text-xs text-ink-muted">
          {hint}
        </p>
      )}

      <input
        id={id}
        type={type}
        value={value}
        onChange={(event) => onChange(event.target.value)}
        autoComplete={autoComplete}
        inputMode={inputMode}
        aria-invalid={error ? true : undefined}
        aria-describedby={describedBy}
        className={`mt-2 w-full rounded-lg border bg-white px-3.5 py-2.5 text-base text-ink outline-none transition-colors placeholder:text-ink-muted focus:border-brand-blue focus:ring-2 focus:ring-brand-blue/20 ${
          error ? "border-red-500" : "border-line"
        }`}
      />

      {error && (
        <p id={errorId} className="mt-1.5 text-sm text-red-600">
          {error}
        </p>
      )}
    </div>
  );
}

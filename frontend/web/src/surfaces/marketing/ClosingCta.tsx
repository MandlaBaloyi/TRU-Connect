import type { ReactNode } from "react";

/**
 * The band that closes a page: one heading, one line, the buttons.
 *
 * Every marketing page ends by sending the reader to one of the two
 * doors -- get the app, or sign in as a supplier -- and this is the
 * shape that does it. Pass the buttons in; the page owns the
 * destination.
 */
export function ClosingCta({
  heading,
  body,
  actions,
  onBrand = false,
}: {
  heading: string;
  body?: ReactNode;
  actions: ReactNode;
  onBrand?: boolean;
}) {
  return (
    <div
      className={`rounded-3xl p-10 text-center sm:p-14 ${
        onBrand ? "bg-brand-blue" : "bg-white shadow-sm ring-1 ring-line/60"
      }`}
    >
      <h2
        className={`text-balance text-2xl font-bold tracking-tight sm:text-3xl ${
          onBrand ? "text-white" : "text-brand-blue"
        }`}
      >
        {heading}
      </h2>
      {body && (
        <p
          className={`mx-auto mt-4 max-w-xl leading-relaxed ${
            onBrand ? "text-white/75" : "text-ink-muted"
          }`}
        >
          {body}
        </p>
      )}
      <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
        {actions}
      </div>
    </div>
  );
}

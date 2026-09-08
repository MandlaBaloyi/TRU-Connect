import type { ReactNode } from "react";

/**
 * The top of an interior page: a small eyebrow, the title, and an
 * optional lead paragraph.
 *
 * Separate from the landing/supplier heroes, which carry buttons and
 * sit on colour. This is the quieter version for About, Contact and the
 * legal pages -- one job, set once, so those pages open the same way.
 */
export function PageHeading({
  eyebrow,
  title,
  lead,
  align = "left",
}: {
  eyebrow?: string;
  title: string;
  lead?: ReactNode;
  align?: "left" | "center";
}) {
  const centered = align === "center";
  return (
    <div className={centered ? "mx-auto max-w-2xl text-center" : "max-w-2xl"}>
      {eyebrow && (
        <p className="text-sm font-semibold uppercase tracking-wider text-brand-green">
          {eyebrow}
        </p>
      )}
      <h1 className="mt-3 text-pretty text-4xl font-bold tracking-tight text-brand-blue sm:text-5xl">
        {title}
      </h1>
      {lead && (
        <p className="mt-5 text-lg leading-relaxed text-ink-muted">{lead}</p>
      )}
    </div>
  );
}

import type { ElementType, ReactNode } from "react";

/**
 * The horizontal frame every section shares: a centred column with the
 * same max width and the same gutter, so nothing on the page defines
 * its own edge by hand.
 *
 * `wide` is the default (the marketing content width). `narrow` is for
 * long-form reading -- the legal pages -- where a full-width measure is
 * too wide to follow.
 */
export function Container({
  as: Tag = "div",
  width = "wide",
  className = "",
  children,
}: {
  as?: ElementType;
  width?: "wide" | "narrow";
  className?: string;
  children: ReactNode;
}) {
  const max = width === "narrow" ? "max-w-3xl" : "max-w-6xl";
  return (
    <Tag className={`mx-auto w-full ${max} px-5 ${className}`.trim()}>
      {children}
    </Tag>
  );
}

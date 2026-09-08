import type { ElementType, ReactNode } from "react";

import { Container } from "@/design-system/primitives/Container";

/**
 * A vertical band of the page: consistent top-and-bottom rhythm, an
 * optional background tone, and an optional hairline to separate it from
 * its neighbours.
 *
 * A pattern rather than a primitive because it composes `Container` and
 * decides spacing -- the recurring *shape* a page is built from. Every
 * marketing section goes through here so the page has one rhythm instead
 * of a dozen hand-picked `py-` values.
 */

type Tone = "plain" | "wash" | "brand";

const TONES: Record<Tone, string> = {
  plain: "bg-white text-ink",
  wash: "bg-wash text-ink",
  brand: "bg-brand-blue text-white",
};

const SPACE = {
  sm: "py-12 sm:py-16",
  md: "py-16 sm:py-20",
  lg: "py-20 sm:py-28",
} as const;

export function Section({
  as: Tag = "section",
  tone = "plain",
  space = "md",
  divide = false,
  width = "wide",
  id,
  className = "",
  children,
}: {
  as?: ElementType;
  tone?: Tone;
  space?: keyof typeof SPACE;
  /** Draw a hairline above and below. Reads well between two same-tone bands. */
  divide?: boolean;
  width?: "wide" | "narrow";
  id?: string;
  className?: string;
  children: ReactNode;
}) {
  const border = divide ? "border-y border-line/60" : "";
  // scroll-mt keeps an anchored section clear of the sticky header.
  const anchor = id ? "scroll-mt-20" : "";
  return (
    <Tag
      id={id}
      className={`${TONES[tone]} ${border} ${anchor} ${className}`.trim()}
    >
      <Container width={width} className={SPACE[space]}>
        {children}
      </Container>
    </Tag>
  );
}

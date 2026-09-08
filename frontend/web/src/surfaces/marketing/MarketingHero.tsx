import type { ReactNode } from "react";

import { Container } from "@/design-system/primitives/Container";
import { CloudinaryImage } from "@/surfaces/marketing/CloudinaryImage";
import type { MarketingImageKey } from "@/surfaces/marketing/imagery";

/**
 * The top of the landing and supplier pages: the eyebrow, the headline,
 * one paragraph, the call-to-action buttons, and -- when there is one --
 * the photo beside it.
 *
 * Two tones. `light` sits on the page background; `brand` sits on navy,
 * which is what the supplier page uses to set itself apart from the
 * business-facing home page. Pass the buttons in as `actions` so each
 * page keeps ownership of where its doors lead.
 */
export function MarketingHero({
  eyebrow,
  title,
  lead,
  actions,
  image,
  tone = "light",
}: {
  eyebrow: string;
  title: ReactNode;
  lead: ReactNode;
  actions?: ReactNode;
  image?: MarketingImageKey;
  tone?: "light" | "brand";
}) {
  const brand = tone === "brand";

  return (
    <section
      className={
        brand
          ? "bg-brand-blue"
          : "border-b border-line/60 bg-gradient-to-b from-wash to-white"
      }
    >
      <Container className="py-16 sm:py-24">
        <div
          className={
            image
              ? "grid items-center gap-12 lg:grid-cols-2 lg:gap-16"
              : "max-w-3xl"
          }
        >
          <div>
            <p
              className={`text-sm font-semibold uppercase tracking-wider ${
                brand ? "text-brand-green-light" : "text-brand-green"
              }`}
            >
              {eyebrow}
            </p>
            <h1
              className={`mt-4 text-balance text-4xl font-bold leading-[1.1] tracking-tight sm:text-5xl lg:text-6xl ${
                brand ? "text-white" : "text-brand-blue"
              }`}
            >
              {title}
            </h1>
            <p
              className={`mt-6 max-w-xl text-lg leading-relaxed ${
                brand ? "text-white/75" : "text-ink-muted"
              }`}
            >
              {lead}
            </p>
            {actions && (
              <div className="mt-9 flex flex-col gap-3 sm:flex-row sm:items-center">
                {actions}
              </div>
            )}
          </div>

          {image && (
            <div className="lg:pl-4">
              <CloudinaryImage
                image={image}
                priority
                sizes="(min-width: 1024px) 42rem, 100vw"
                options={{ gravity: "auto" }}
                className="shadow-xl ring-1 ring-black/5"
              />
            </div>
          )}
        </div>
      </Container>
    </section>
  );
}

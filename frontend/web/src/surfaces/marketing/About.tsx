import Link from "next/link";

import { buttonClass } from "@/design-system/primitives/Button";
import { PageHeading } from "@/design-system/primitives/PageHeading";
import { Section } from "@/design-system/patterns/Section";
import { routes } from "@/config/routes";
import { CloudinaryImage } from "@/surfaces/marketing/CloudinaryImage";
import { ClosingCta } from "@/surfaces/marketing/ClosingCta";
import { GetTheApp } from "@/surfaces/marketing/GetTheApp";

/**
 * About TruConnect.
 *
 * KEPT MODEST ON PURPOSE. This page says what the product is and who
 * builds it -- not how big it is or how many people use it. Every
 * sentence here should still be true in six months. The two doors at the
 * bottom are the same two doors as everywhere else.
 */

const PRINCIPLES = [
  {
    title: "A record both sides can trust",
    body: "An order, a price, a payment method, a status -- written once, the same way for the business and the supplier. That shared record is the product.",
  },
  {
    title: "The phone is the business's whole surface",
    body: "A shop owner's phone is with them all day and their work does not happen at a desk. There is no business website to sign into because there is nothing a desk would add.",
  },
  {
    title: "Claim only what is built",
    body: "Features arrive on these pages when they ship, not when they are planned. A supplier who signs up for something that is not there yet is worse off than one who never heard of it.",
  },
];

export function About() {
  return (
    <>
      <Section space="lg">
        <PageHeading
          eyebrow="About"
          title="A supply network for the informal economy."
          lead={
            <>
              TruConnect connects South Africa&rsquo;s spaza shops, salons and
              small retailers with the suppliers who stock them. It is part of
              TruePoint, a platform being built for the businesses that keep
              their neighbourhoods supplied.
            </>
          }
        />
      </Section>

      <Section tone="wash" divide space="lg">
        <div className="grid items-center gap-12 lg:grid-cols-2 lg:gap-16">
          <div className="order-2 lg:order-1">
            <h2 className="text-balance text-3xl font-bold tracking-tight text-brand-blue sm:text-4xl">
              Why it exists
            </h2>
            <div className="mt-5 space-y-4 leading-relaxed text-ink-muted">
              <p>
                Restocking an independent business runs on voice notes, memory
                and trust. It mostly works &mdash; until a price changes without
                warning, or stock that was promised was never there, or a
                week-old order needs to be reconstructed from a chat thread.
              </p>
              <p>
                TruConnect puts the parts that need to be reliable &mdash; the
                catalogue, the per-unit price, the order, the history &mdash; in
                one place both sides can see. The relationship stays between the
                business and the supplier; the record stops being something
                either of them has to keep by hand.
              </p>
            </div>
          </div>
          <div className="order-1 lg:order-2">
            <CloudinaryImage
              image="aboutStory"
              sizes="(min-width: 1024px) 32rem, 100vw"
              className="shadow-xl ring-1 ring-black/5"
            />
          </div>
        </div>
      </Section>

      <Section space="lg">
        <h2 className="max-w-2xl text-balance text-3xl font-bold tracking-tight text-brand-blue sm:text-4xl">
          What we hold to
        </h2>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {PRINCIPLES.map((p) => (
            <div
              key={p.title}
              className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-line/60"
            >
              <h3 className="text-lg font-semibold text-brand-blue">
                {p.title}
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-ink-muted">
                {p.body}
              </p>
            </div>
          ))}
        </div>
      </Section>

      <Section tone="wash" divide space="lg">
        <ClosingCta
          heading="Two ways in."
          body="Buying stock for a shop happens in the app. Supplying it starts on the web."
          actions={
            <>
              <GetTheApp />
              <Link
                href={routes.suppliers}
                className={buttonClass({ variant: "secondary" })}
              >
                I&rsquo;m a supplier
              </Link>
            </>
          }
        />
      </Section>
    </>
  );
}

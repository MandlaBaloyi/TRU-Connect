import Link from "next/link";

import { buttonClass } from "@/design-system/primitives/Button";
import { PageHeading } from "@/design-system/primitives/PageHeading";
import { Section } from "@/design-system/patterns/Section";
import { CatalogueRoutes } from "@/surfaces/marketing/CatalogueRoutes";
import { routes } from "@/config/routes";

/**
 * How the platform works, told twice -- once for each side.
 *
 * TWO SEPARATE WALKTHROUGHS RATHER THAN ONE NEUTRAL ONE, because the two
 * sides do genuinely different things and a single "how it works" that
 * serves both ends up describing neither. A shop owner wants to know how
 * they find and order stock; a wholesaler wants to know what arrives on
 * their side and what they have to do about it.
 *
 * NOTHING HERE DESCRIBES A FEATURE THAT DOES NOT EXIST. Every step below
 * is something the platform does today.
 */

const BUSINESS_STEPS = [
  {
    title: "Find suppliers who stock what you sell",
    body: "Browse by category or search for a wholesaler you already buy from. You do not need an introduction to look, and you do not need permission to see prices.",
  },
  {
    title: "See what a unit actually costs",
    body: "Pack sizes are made comparable, so a case of 6 and a case of 12 line up and you can tell which is genuinely cheaper — not just which looks it.",
  },
  {
    title: "Order, and keep the record",
    body: "Place the order, agree how you are paying, and both you and the supplier end up with the same history afterwards. No reconstructing a WhatsApp thread.",
  },
];

const SUPPLIER_STEPS = [
  {
    title: "Get your products in",
    body: "Type them, upload the price file you already have, or connect your own system. Re-upload that file whenever prices change and your listings update in place rather than duplicating.",
  },
  {
    title: "Set your own terms",
    body: "Minimum order, delivery or collection, which payment methods you take, what businesses can see about you, and whether they need your approval before ordering at all.",
  },
  {
    title: "Take orders where you actually are",
    body: "Orders reach you on your phone. Cash orders wait for your decision, because you are releasing stock against a promise. Once card payments arrive, those will not need approving — the money will already have moved.",
  },
];

function Steps({ steps }: { steps: { title: string; body: string }[] }) {
  return (
    <ol className="mt-10 space-y-8">
      {steps.map((step, index) => (
        <li key={step.title} className="flex gap-5">
          <span
            aria-hidden
            className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-blue text-sm font-bold text-white"
          >
            {index + 1}
          </span>
          <div>
            <h3 className="text-lg font-semibold text-ink">{step.title}</h3>
            <p className="mt-2 leading-relaxed text-ink-muted">{step.body}</p>
          </div>
        </li>
      ))}
    </ol>
  );
}

export function HowItWorks() {
  return (
    <>
      <Section space="lg">
        <PageHeading
          eyebrow="How it works"
          title="Two sides, one record."
          lead="A business finds stock and orders it. A supplier lists what they carry and fulfils it. The part that matters is that both end up looking at the same thing afterwards."
        />
      </Section>

      <Section tone="wash" divide space="lg" width="narrow">
        <p className="text-sm font-semibold uppercase tracking-wider text-brand-green">
          If you run a shop
        </p>
        <h2 className="mt-3 text-3xl font-bold tracking-tight text-brand-blue">
          Restocking, on your phone
        </h2>
        <Steps steps={BUSINESS_STEPS} />
        <p className="mt-10 text-sm text-ink-muted">
          Everything on this side happens in the app. There is nothing for a business to do on a
          computer, so we have not built one.
        </p>
      </Section>

      <Section space="lg" width="narrow">
        <p className="text-sm font-semibold uppercase tracking-wider text-brand-green">
          If you supply shops
        </p>
        <h2 className="mt-3 text-3xl font-bold tracking-tight text-brand-blue">
          Set up once, run it from anywhere
        </h2>
        <Steps steps={SUPPLIER_STEPS} />
        <p className="mt-10 text-sm text-ink-muted">
          Setting up is desk work and belongs on a screen with a keyboard. Running the day is not,
          and belongs on your phone. You get both.
        </p>
      </Section>

      <CatalogueRoutes />

      <Section space="lg">
        <div className="rounded-2xl border border-line/70 bg-white p-10 text-center">
          <h2 className="text-2xl font-bold tracking-tight text-brand-blue sm:text-3xl">
            Ready to list your products?
          </h2>
          <p className="mx-auto mt-4 max-w-xl leading-relaxed text-ink-muted">
            Create an account and add what you carry. Nothing goes live until you say so.
          </p>
          <div className="mt-8 flex flex-col justify-center gap-3 sm:flex-row">
            <Link href={routes.signUp} className={buttonClass()}>
              Create a supplier account
            </Link>
            <Link href={routes.contact} className={buttonClass({ variant: "secondary" })}>
              Contact sales
            </Link>
          </div>
        </div>
      </Section>
    </>
  );
}

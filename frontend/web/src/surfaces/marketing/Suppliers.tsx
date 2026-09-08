import Link from "next/link";

import { buttonClass } from "@/design-system/primitives/Button";
import { Section } from "@/design-system/patterns/Section";
import { CatalogueRoutes } from "@/surfaces/marketing/CatalogueRoutes";
import { routes } from "@/config/routes";
import { ClosingCta } from "@/surfaces/marketing/ClosingCta";
import { InfoCardGrid } from "@/surfaces/marketing/InfoCardGrid";
import { MarketingHero } from "@/surfaces/marketing/MarketingHero";

/**
 * The "For suppliers" page body -- the agreed route from the public site
 * into the portal. Footer link, header link, and both landing-page hero
 * buttons all land here, and this page has exactly one job: get a
 * supplier to sign up or sign in.
 *
 * WHAT IT CLAIMS IS WHAT EXISTS. Catalogue, storefront sections,
 * fulfilment terms, order handling and visibility controls are built and
 * working in the app today. Bulk import, price files and system
 * integration are real plans but are NOT on this page -- a supplier who
 * signs up for a promised feature and does not find it is worse than one
 * who never heard about it.
 */

const VALUE = [
  {
    title: "Reach shops already buying your stock",
    body: "Businesses browse and find you without an introduction. You choose whether they need your approval before they can order.",
  },
  {
    title: "Your catalogue, your prices",
    body: "List what you carry with real prices and pack sizes. Put what is on sale, what sells most, and what you want moved at the top of your profile.",
  },
  {
    title: "Your own terms",
    body: "Minimum order, delivery or collection, which payment methods you accept, and what contact details you show. All yours to set.",
  },
  {
    title: "A record on both sides",
    body: "Every order is written down the same way for you and the buyer. No more reconstructing a WhatsApp thread.",
  },
];

export function Suppliers() {
  return (
    <>
      <MarketingHero
        tone="brand"
        eyebrow="For suppliers"
        title="Sell to the shops that already stock what you sell."
        lead={
          <>
            Set your catalogue up here, where you have a keyboard and your price
            list. Then run the day from the app &mdash; orders, decisions, and
            notifications, wherever you are.
          </>
        }
        image="suppliersHero"
        actions={
          <>
            <Link
              href={routes.signUp}
              className={buttonClass({ variant: "accent", onBrand: true })}
            >
              Create a supplier account
            </Link>
            <Link
              href={routes.signIn}
              className={buttonClass({ variant: "secondary", onBrand: true })}
            >
              I already have an account
            </Link>
          </>
        }
      />

      <Section space="lg">
        <InfoCardGrid heading="What you get" cards={VALUE} columns={2} />
      </Section>

      {/* Two surfaces -- the split is by task, not by supplier size. */}
      <Section tone="wash" divide space="lg">
        <h2 className="max-w-2xl text-balance text-3xl font-bold tracking-tight text-brand-blue sm:text-4xl">
          Two places, two jobs
        </h2>
        <p className="mt-4 max-w-2xl text-lg leading-relaxed text-ink-muted">
          Whatever size you are, you get both. Which one you spend more time in
          is up to how you work.
        </p>

        <div className="mt-12 grid gap-6 md:grid-cols-2">
          <div className="rounded-2xl bg-white p-7 shadow-sm ring-1 ring-line/60">
            <h3 className="text-sm font-bold uppercase tracking-wider text-brand-green">
              On the web
            </h3>
            <p className="mt-3 text-lg font-semibold text-ink">
              Setting up, and keeping it current
            </p>
            <p className="mt-3 text-sm leading-relaxed text-ink-muted">
              Your catalogue, your prices, how you fulfil orders, and how your
              profile looks to a business. Desk work, on a screen big enough for
              it.
            </p>
          </div>

          <div className="rounded-2xl bg-white p-7 shadow-sm ring-1 ring-line/60">
            <h3 className="text-sm font-bold uppercase tracking-wider text-brand-green">
              In the app
            </h3>
            <p className="mt-3 text-lg font-semibold text-ink">
              Running the day
            </p>
            <p className="mt-3 text-sm leading-relaxed text-ink-muted">
              Orders coming in, decisions on cash payments, and knowing straight
              away when something needs you. On you, all day.
            </p>
          </div>
        </div>
      </Section>

      <CatalogueRoutes />

      <Section space="lg">
        <ClosingCta
          heading="Getting listed takes minutes."
          body="Create your account, add what you carry, and set your terms. You decide what businesses can see before anything goes live."
          actions={
            <Link href={routes.signUp} className={buttonClass()}>
              Create a supplier account
            </Link>
          }
        />
      </Section>
    </>
  );
}

import Link from "next/link";

import { buttonClass } from "@/design-system/primitives/Button";
import { Section } from "@/design-system/patterns/Section";
import { CatalogueRoutes } from "@/surfaces/marketing/CatalogueRoutes";
import { routes } from "@/config/routes";
import { ClosingCta } from "@/surfaces/marketing/ClosingCta";
import { GetTheApp } from "@/surfaces/marketing/GetTheApp";
import { InfoCardGrid } from "@/surfaces/marketing/InfoCardGrid";
import { MarketingHero } from "@/surfaces/marketing/MarketingHero";

/**
 * The public landing page body.
 *
 * IT SPEAKS TO TWO AUDIENCES WITH TWO DIFFERENT ENDINGS. A business
 * leaves for the app store; a supplier leaves for /suppliers and then a
 * sign-up. Every section is arranged to move one of those two people to
 * the right door, and nothing else is on the page.
 *
 * The copy here is deliberately plain and replaceable -- it can change
 * the day the positioning changes. The structure is what this file
 * owns.
 */

const PROBLEMS = [
  {
    title: "Orders live in WhatsApp",
    body: "A voice note, three photos and a phone call. Nobody can find what was agreed a week later, and neither side has a record when it goes wrong.",
  },
  {
    title: "Prices move without warning",
    body: "You find out the case price changed when the invoice arrives. Comparing two suppliers means remembering what each of them said.",
  },
  {
    title: "Stock runs out quietly",
    body: "You order, then wait, then find out it was never in stock. The trip is wasted and the shelf stays empty.",
  },
];

const STEPS = [
  {
    title: "Find suppliers who stock what you sell",
    body: "Browse by category or search a supplier you already buy from. You do not need an introduction to look.",
  },
  {
    title: "See the real price, per unit",
    body: "Pack sizes made comparable. A case of 6 and a case of 12 line up, so you can see which one is actually cheaper.",
  },
  {
    title: "Order, and keep the record",
    body: "Place the order, agree the payment, and both sides have the same history afterwards.",
  },
];

export function Landing() {
  return (
    <>
      <MarketingHero
        eyebrow="Built in South Africa"
        title="The supply network for independent businesses."
        lead={
          <>
            TruConnect connects spaza shops, salons and small retailers with the
            suppliers who stock them &mdash; with real prices, real stock, and a
            record of every order.
          </>
        }
        image="homeHero"
        actions={
          <>
            <Link href="/#how-it-works" className={buttonClass()}>
              See how it works
            </Link>
            <Link
              href={routes.suppliers}
              className={buttonClass({ variant: "secondary" })}
            >
              I&rsquo;m a supplier
            </Link>
          </>
        }
      />

      <Section space="lg">
        <InfoCardGrid
          heading="Restocking is harder than it should be."
          cards={PROBLEMS}
        />
      </Section>

      <Section id="how-it-works" tone="wash" divide space="lg">
        <InfoCardGrid
          heading="How it works"
          intro="For the business, it happens on a phone. Three steps, and none of them is a phone call."
          cards={STEPS}
          numbered
        />
      </Section>

      <Section space="lg">
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Businesses -- the app is the whole product for them. */}
          <div className="rounded-3xl bg-white p-8 shadow-sm ring-1 ring-line/60">
            <h2 className="text-2xl font-bold tracking-tight text-brand-blue">
              For businesses
            </h2>
            <p className="mt-3 leading-relaxed text-ink-muted">
              Everything happens in the app, because your phone is already with
              you all day. Find suppliers, compare what a unit actually costs,
              place an order, and keep the history.
            </p>
            <div className="mt-6">
              <GetTheApp size="md" />
            </div>
          </div>

          {/* Suppliers -- the web is the setup surface, the app is daily. */}
          <div className="rounded-3xl bg-brand-blue p-8 text-white">
            <h2 className="text-2xl font-bold tracking-tight">For suppliers</h2>
            <p className="mt-3 leading-relaxed text-white/75">
              Set up your catalogue on the web, where you have a keyboard and
              your price file. Then run the day from the app &mdash; orders,
              decisions, and notifications, wherever you are.
            </p>
            <Link
              href={routes.suppliers}
              className={`mt-6 ${buttonClass({ variant: "accent", size: "md", onBrand: true })}`}
            >
              See what suppliers get
            </Link>
          </div>
        </div>
      </Section>

      <CatalogueRoutes tone="plain" />

      <Section tone="wash" divide space="lg">
        <ClosingCta
          heading="Two people, one supply chain that finally has a record."
          body="A business gets the app. A supplier starts on the web."
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

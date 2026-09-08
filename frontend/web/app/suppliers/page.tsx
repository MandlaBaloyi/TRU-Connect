import type { Metadata } from "next";
import Link from "next/link";

/**
 * The "For suppliers" page -- the agreed route from the public site into
 * the portal. Footer link, header link, and both hero buttons on the
 * landing page all land here, and this page has exactly one job: get a
 * supplier to sign up or sign in.
 *
 * WHAT IT CLAIMS IS WHAT EXISTS. Everything described below is built and
 * working in the app today -- catalogue, storefront sections, fulfilment
 * terms, order handling, visibility controls. Bulk import, price files
 * and system integration are real plans but they are NOT on this page,
 * because a supplier who signs up for a promised feature and does not
 * find it is worse than one who never heard about it.
 */

export const metadata: Metadata = {
  title: "For suppliers",
  description:
    "Reach the shops already buying what you sell. Set your catalogue up on the web, run the day from the app, and keep your own terms.",
};

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

export default function SuppliersPage() {
  return (
    <>
      {/* HERO */}
      <section className="border-b border-line/60 bg-brand-blue">
        <div className="mx-auto max-w-6xl px-5 py-20 sm:py-24">
          <p className="text-sm font-semibold uppercase tracking-wider text-brand-green-light">
            For suppliers
          </p>
          <h1 className="mt-4 max-w-3xl text-4xl font-bold leading-[1.15] tracking-tight text-white sm:text-5xl">
            Sell to the shops that already stock what you sell.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-relaxed text-white/75">
            Set your catalogue up here, where you have a keyboard and your
            price list. Then run the day from the app &mdash; orders,
            decisions, and notifications, wherever you are.
          </p>

          <div className="mt-9 flex flex-col gap-3 sm:flex-row sm:items-center">
            <Link
              href="/sign-up"
              className="inline-flex items-center justify-center rounded-lg bg-brand-green px-6 py-3.5 text-base font-semibold text-white transition-colors hover:bg-brand-green-dark focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            >
              Create a supplier account
            </Link>
            <Link
              href="/sign-in"
              className="inline-flex items-center justify-center rounded-lg border border-white/30 px-6 py-3.5 text-base font-semibold text-white transition-colors hover:bg-white/10 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            >
              I already have an account
            </Link>
          </div>
        </div>
      </section>

      {/* VALUE */}
      <section className="mx-auto max-w-6xl px-5 py-20">
        <div className="grid gap-6 md:grid-cols-2">
          {VALUE.map((item) => (
            <div
              key={item.title}
              className="rounded-xl border border-line/70 bg-white p-7"
            >
              <h2 className="text-lg font-semibold text-brand-blue">
                {item.title}
              </h2>
              <p className="mt-3 text-sm leading-relaxed text-ink-muted">
                {item.body}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* TWO SURFACES -- the split is by task, not by supplier size. */}
      <section className="border-y border-line/60 bg-wash">
        <div className="mx-auto max-w-6xl px-5 py-20">
          <h2 className="text-3xl font-bold tracking-tight text-brand-blue sm:text-4xl">
            Two places, two jobs
          </h2>
          <p className="mt-4 max-w-2xl text-lg text-ink-muted">
            Whatever size you are, you get both. Which one you spend more time
            in is up to how you work.
          </p>

          <div className="mt-12 grid gap-6 md:grid-cols-2">
            <div className="rounded-xl border border-line/70 bg-white p-7">
              <h3 className="text-sm font-bold uppercase tracking-wider text-brand-green">
                On the web
              </h3>
              <p className="mt-3 text-lg font-semibold text-ink">
                Setting up, and keeping it current
              </p>
              <p className="mt-3 text-sm leading-relaxed text-ink-muted">
                Your catalogue, your prices, how you fulfil orders, and how
                your profile looks to a business. Desk work, on a screen big
                enough for it.
              </p>
            </div>

            <div className="rounded-xl border border-line/70 bg-white p-7">
              <h3 className="text-sm font-bold uppercase tracking-wider text-brand-green">
                In the app
              </h3>
              <p className="mt-3 text-lg font-semibold text-ink">
                Running the day
              </p>
              <p className="mt-3 text-sm leading-relaxed text-ink-muted">
                Orders coming in, decisions on cash payments, and knowing
                straight away when something needs you. On you, all day.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CLOSING CTA */}
      <section className="mx-auto max-w-6xl px-5 py-20">
        <div className="rounded-2xl border border-line/70 bg-white p-10 text-center">
          <h2 className="text-2xl font-bold tracking-tight text-brand-blue sm:text-3xl">
            Getting listed takes minutes.
          </h2>
          <p className="mx-auto mt-4 max-w-xl leading-relaxed text-ink-muted">
            Create your account, add what you carry, and set your terms. You
            decide what businesses can see before anything goes live.
          </p>
          <Link
            href="/sign-up"
            className="mt-8 inline-flex items-center justify-center rounded-lg bg-brand-blue px-7 py-3.5 text-base font-semibold text-white transition-colors hover:bg-brand-blue-light focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-blue"
          >
            Create a supplier account
          </Link>
        </div>
      </section>
    </>
  );
}

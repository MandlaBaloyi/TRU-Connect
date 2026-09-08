import Link from "next/link";

/**
 * The public landing page.
 *
 * WRITTEN TO BE REPLACED. It is pure frontend with no backend coupling,
 * so it can change the day the positioning changes, and it does not need
 * to be right on the first pass -- which is exactly why it was built
 * first, ahead of the portal it leads into.
 *
 * IT SPEAKS TO TWO AUDIENCES WITH TWO DIFFERENT ENDINGS. A business
 * leaves for the app store; a supplier leaves for /suppliers and then a
 * sign-up. Every section below is arranged around getting one of those
 * two people to the right door, and nothing else is on the page.
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
    n: "01",
    title: "Find suppliers who stock what you sell",
    body: "Browse by category or search a supplier you already buy from. You do not need an introduction to look.",
  },
  {
    n: "02",
    title: "See the real price, per unit",
    body: "Pack sizes made comparable. A case of 6 and a case of 12 line up, so you can see which one is actually cheaper.",
  },
  {
    n: "03",
    title: "Order, and keep the record",
    body: "Place the order, agree the payment, and both sides have the same history afterwards.",
  },
];

export default function HomePage() {
  return (
    <>
      {/* HERO */}
      <section className="border-b border-line/60 bg-gradient-to-b from-wash to-white">
        <div className="mx-auto max-w-6xl px-5 py-20 sm:py-28">
          <p className="text-sm font-semibold uppercase tracking-wider text-brand-green">
            Built in South Africa
          </p>
          <h1 className="mt-4 max-w-3xl text-4xl font-bold leading-[1.1] tracking-tight text-brand-blue sm:text-5xl lg:text-6xl">
            The supply network for independent businesses.
          </h1>
          <p className="mt-6 max-w-2xl text-lg leading-relaxed text-ink-muted">
            TruConnect connects spaza shops, salons and small retailers with
            the suppliers who stock them &mdash; with real prices, real stock,
            and a record of every order.
          </p>

          <div className="mt-9 flex flex-col gap-3 sm:flex-row sm:items-center">
            <Link
              href="/#how-it-works"
              className="inline-flex items-center justify-center rounded-lg bg-brand-blue px-6 py-3.5 text-base font-semibold text-white transition-colors hover:bg-brand-blue-light focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-blue"
            >
              See how it works
            </Link>
            <Link
              href="/suppliers"
              className="inline-flex items-center justify-center rounded-lg border border-line bg-white px-6 py-3.5 text-base font-semibold text-brand-blue transition-colors hover:border-brand-blue hover:bg-wash focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-blue"
            >
              I&rsquo;m a supplier
            </Link>
          </div>
        </div>
      </section>

      {/* THE PROBLEM */}
      <section className="mx-auto max-w-6xl px-5 py-20">
        <h2 className="max-w-2xl text-3xl font-bold tracking-tight text-brand-blue sm:text-4xl">
          Restocking is harder than it should be.
        </h2>
        <div className="mt-12 grid gap-6 md:grid-cols-3">
          {PROBLEMS.map((problem) => (
            <div
              key={problem.title}
              className="rounded-xl border border-line/70 bg-white p-6"
            >
              <h3 className="text-lg font-semibold text-ink">
                {problem.title}
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-ink-muted">
                {problem.body}
              </p>
            </div>
          ))}
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section
        id="how-it-works"
        className="scroll-mt-16 border-y border-line/60 bg-wash"
      >
        <div className="mx-auto max-w-6xl px-5 py-20">
          <h2 className="text-3xl font-bold tracking-tight text-brand-blue sm:text-4xl">
            How it works
          </h2>
          <p className="mt-4 max-w-2xl text-lg text-ink-muted">
            For the business, it happens on a phone. Three steps, and none of
            them is a phone call.
          </p>

          <ol className="mt-12 grid gap-8 md:grid-cols-3">
            {STEPS.map((step) => (
              <li key={step.n}>
                <span className="text-sm font-bold tracking-wider text-brand-green">
                  {step.n}
                </span>
                <h3 className="mt-3 text-lg font-semibold text-ink">
                  {step.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-ink-muted">
                  {step.body}
                </p>
              </li>
            ))}
          </ol>
        </div>
      </section>

      {/* TWO AUDIENCES */}
      <section className="mx-auto max-w-6xl px-5 py-20">
        <div className="grid gap-6 lg:grid-cols-2">
          {/* Businesses -- the app is the whole product for them. */}
          <div className="rounded-2xl border border-line/70 bg-white p-8">
            <h2 className="text-2xl font-bold tracking-tight text-brand-blue">
              For businesses
            </h2>
            <p className="mt-3 leading-relaxed text-ink-muted">
              Everything happens in the app, because your phone is already with
              you all day. Find suppliers, compare what a unit actually costs,
              place an order, and keep the history.
            </p>
            <p className="mt-6 text-sm font-semibold text-ink">
              Coming to Android and iPhone.
            </p>
          </div>

          {/* Suppliers -- the web is the setup surface, the app is daily. */}
          <div className="rounded-2xl border border-brand-blue bg-brand-blue p-8 text-white">
            <h2 className="text-2xl font-bold tracking-tight">
              For suppliers
            </h2>
            <p className="mt-3 leading-relaxed text-white/75">
              Set up your catalogue on the web, where you have a keyboard and
              your price file. Then run the day from the app &mdash; orders,
              decisions, and notifications, wherever you are.
            </p>
            <Link
              href="/suppliers"
              className="mt-6 inline-flex items-center justify-center rounded-lg bg-brand-green px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-brand-green-dark focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-white"
            >
              See what suppliers get
            </Link>
          </div>
        </div>
      </section>
    </>
  );
}

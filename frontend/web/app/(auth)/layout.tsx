import Link from "next/link";

import { Logo } from "@/design-system/primitives/Logo";
import { routes } from "@/config/routes";

/**
 * The AUTH shell: form on the left, brand panel on the right.
 *
 * A SPLIT RATHER THAN A BARE COLUMN, and the reason is not decoration.
 * The previous version put a form on an empty white page, which reads as
 * unfinished -- and the person reading it is a wholesaler deciding
 * whether this platform is real enough to move their catalogue onto.
 * The panel uses space that was doing nothing to answer the question
 * they are actually holding: what do I get for this.
 *
 * THE PANEL DISAPPEARS ON MOBILE. It is reassurance, not instruction,
 * and on a phone it would push the form below the fold -- which costs a
 * sign-up to save a paragraph nobody asked for.
 *
 * STILL NO SITE NAVIGATION. Someone on a sign-in page has one job, and a
 * full marketing header offers them eight other things to click. What
 * this adds instead is the two escapes that are genuinely useful: the
 * logo home, and a way to reach a person -- because a supplier who
 * cannot complete a sign-up should be able to talk to someone rather
 * than close the tab.
 */

const PANEL_POINTS = [
  {
    title: "Your catalogue, however you keep it",
    body: "Type it in, upload the price file you already have, or connect your own system.",
  },
  {
    title: "Your terms, not ours",
    body: "Minimum order, delivery or collection, which payments you take, and what businesses can see.",
  },
  {
    title: "Nothing goes live until you say so",
    body: "Set everything up privately. You decide when your shopfront opens.",
  },
];

export default function AuthLayout({ children }: LayoutProps<"/">) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-line/60 bg-white">
        <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-5">
          <Link
            href={routes.home}
            className="rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-brand-blue"
          >
            <Logo className="text-xl" />
          </Link>
          <Link
            href={routes.contact}
            className="rounded-md px-3 py-2 text-sm font-medium text-ink-muted transition-colors hover:text-ink"
          >
            Need help? <span className="text-brand-blue">Talk to us</span>
          </Link>
        </div>
      </header>

      <div className="flex flex-1 flex-col lg:flex-row">
        <main className="flex flex-1 items-center justify-center px-5 py-12 sm:py-16">
          <div className="w-full max-w-md">{children}</div>
        </main>

        <aside className="hidden bg-brand-blue px-12 py-16 lg:flex lg:w-[44%] lg:items-center">
          <div className="max-w-sm">
            <p className="text-sm font-semibold uppercase tracking-wider text-brand-green-light">
              For suppliers
            </p>
            <h2 className="mt-3 text-3xl font-bold leading-tight tracking-tight text-white">
              Sell to the shops that already stock what you sell.
            </h2>

            <ul className="mt-10 space-y-7">
              {PANEL_POINTS.map((point) => (
                <li key={point.title} className="flex gap-4">
                  <span
                    aria-hidden
                    className="mt-1.5 h-2 w-2 shrink-0 rounded-full bg-brand-green"
                  />
                  <div>
                    <h3 className="font-semibold text-white">{point.title}</h3>
                    <p className="mt-1 text-sm leading-relaxed text-white/70">{point.body}</p>
                  </div>
                </li>
              ))}
            </ul>

            {/* Businesses land here by mistake often enough to be worth
                one line. Telling them plainly beats letting them try
                credentials that cannot exist. */}
            <p className="mt-12 border-t border-white/15 pt-6 text-sm text-white/60">
              Buying stock for your shop? TruConnect for businesses is in the app — there is nothing
              to sign in to here.
            </p>
          </div>
        </aside>
      </div>
    </div>
  );
}

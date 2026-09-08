import Link from "next/link";

import { Wordmark } from "@/components/ui/Wordmark";

/**
 * The site footer, and the FOR SUPPLIERS column is the point of it.
 *
 * This is the agreed route into the portal: a supplier arrives on the
 * public site, finds "For suppliers" in the footer, and from there can
 * sign up or sign in. The header carries the same path for anyone who
 * looks up rather than down, but the footer is where a visitor who has
 * read the page ends up, so the column is given real estate rather than
 * a single link.
 *
 * Routes marked TODO are deliberately not linked yet. A footer full of
 * dead links reads worse than a short footer, and every one of these is
 * cheap to add the day the page behind it exists.
 */
export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-line/60 bg-wash">
      <div className="mx-auto max-w-6xl px-5 py-14">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
          <div className="lg:col-span-2">
            <Wordmark className="text-lg" />
            <p className="mt-3 max-w-xs text-sm leading-relaxed text-ink-muted">
              The supply network for South Africa&rsquo;s independent
              businesses.
            </p>
          </div>

          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-ink">
              For suppliers
            </h2>
            <ul className="mt-4 space-y-2.5 text-sm">
              <li>
                <Link
                  href="/suppliers"
                  className="text-ink-muted transition-colors hover:text-brand-blue"
                >
                  Why TruConnect
                </Link>
              </li>
              <li>
                <Link
                  href="/sign-up"
                  className="font-semibold text-brand-blue transition-colors hover:text-brand-green"
                >
                  Create a supplier account
                </Link>
              </li>
              <li>
                <Link
                  href="/sign-in"
                  className="text-ink-muted transition-colors hover:text-brand-blue"
                >
                  Supplier sign in
                </Link>
              </li>
            </ul>
          </div>

          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-ink">
              For businesses
            </h2>
            <ul className="mt-4 space-y-2.5 text-sm text-ink-muted">
              <li>Get the app on Android</li>
              <li>Get the app on iPhone</li>
              <li>
                <Link
                  href="/#how-it-works"
                  className="transition-colors hover:text-brand-blue"
                >
                  How it works
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-12 flex flex-col gap-3 border-t border-line/60 pt-6 text-xs text-ink-muted sm:flex-row sm:items-center sm:justify-between">
          <p>
            &copy; {new Date().getFullYear()} TruConnect. A TruePoint platform.
          </p>
          <p>Built in South Africa.</p>
        </div>
      </div>
    </footer>
  );
}

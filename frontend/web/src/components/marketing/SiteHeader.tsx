import Link from "next/link";

import { Wordmark } from "@/components/ui/Wordmark";

/**
 * The public site's top bar.
 *
 * ONE PRIMARY ACTION, and it is the supplier one. Businesses cannot do
 * anything useful on the web (V2_00 section 2.9) -- there is no business
 * sign-in to offer, because there is no business web surface. So the
 * only account action in this bar is "Supplier sign in", and the app is
 * the call to action for everyone else, further down the page where
 * there is room to say who it is for.
 */
export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-line/60 bg-white/85 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-6 px-5">
        <Link href="/" className="shrink-0 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-brand-blue">
          <Wordmark className="text-xl" />
        </Link>

        <nav className="flex items-center gap-1 sm:gap-2">
          <Link
            href="/#how-it-works"
            className="hidden rounded-md px-3 py-2 text-sm font-medium text-ink-muted transition-colors hover:text-ink sm:block"
          >
            How it works
          </Link>
          <Link
            href="/suppliers"
            className="rounded-md px-3 py-2 text-sm font-medium text-ink-muted transition-colors hover:text-ink"
          >
            For suppliers
          </Link>
          <Link
            href="/sign-in"
            className="rounded-lg bg-brand-blue px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-brand-blue-light focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-blue"
          >
            Supplier sign in
          </Link>
        </nav>
      </div>
    </header>
  );
}

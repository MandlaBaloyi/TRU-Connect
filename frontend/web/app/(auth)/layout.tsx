import Link from "next/link";

import { Wordmark } from "@/design-system/primitives/Wordmark";

/**
 * The AUTH shell -- a bare centred column, no site navigation.
 *
 * DELIBERATELY STRIPPED. Someone on a sign-in page has one job, and a
 * full marketing header offers them eight other things to click. The
 * wordmark stays because it is the only thing that says whose login this
 * is, and it links home so nobody is trapped.
 */
export default function AuthLayout({ children }: LayoutProps<"/">) {
  return (
    <div className="flex min-h-screen flex-col">
      <header className="border-b border-line/60">
        <div className="mx-auto flex h-16 max-w-6xl items-center px-5">
          <Link
            href="/"
            className="rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-brand-blue"
          >
            <Wordmark className="text-xl" />
          </Link>
        </div>
      </header>
      <main className="flex-1">{children}</main>
    </div>
  );
}

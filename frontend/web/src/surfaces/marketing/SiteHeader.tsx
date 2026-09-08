import Link from "next/link";

import { buttonClass } from "@/design-system/primitives/Button";
import { Container } from "@/design-system/primitives/Container";
import { Wordmark } from "@/design-system/primitives/Wordmark";
import { routes } from "@/config/routes";

/**
 * The public site's top bar.
 *
 * ONE PRIMARY ACTION, and it is the supplier one. Businesses cannot do
 * anything useful on the web (V2_00 section 2.9) -- there is no business
 * sign-in to offer, because there is no business web surface. So the
 * only account action in this bar is "Supplier sign in", and the app is
 * the call to action for everyone else, further down each page where
 * there is room to say who it is for.
 *
 * The secondary links stay to a count you can read at a glance. Nothing
 * here scrolls to a section on one specific page -- those anchors live
 * in the page body, not the chrome.
 *
 * On a narrow screen only "For suppliers" and the sign-in button show;
 * About and Contact fall to the footer, which every page carries. No
 * hamburger, because a three-item menu does not earn one and a `<details>`
 * disclosure in a sticky bar is worse than the footer link it replaces.
 */

const NAV = [
  { href: routes.suppliers, label: "For suppliers", always: true },
  { href: routes.about, label: "About", always: false },
  { href: routes.contact, label: "Contact", always: false },
];

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-50 border-b border-line/60 bg-white/85 backdrop-blur-sm">
      <Container className="flex h-16 items-center justify-between gap-6">
        <Link
          href={routes.home}
          className="shrink-0 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-brand-blue"
        >
          <Wordmark className="text-xl" />
        </Link>

        <nav className="flex items-center gap-1 sm:gap-2">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className={`rounded-md px-3 py-2 text-sm font-medium text-ink-muted transition-colors hover:text-ink ${
                item.always ? "" : "hidden sm:block"
              }`}
            >
              {item.label}
            </Link>
          ))}
          <Link
            href={routes.signIn}
            className={buttonClass({ variant: "primary", size: "md" })}
          >
            Supplier sign in
          </Link>
        </nav>
      </Container>
    </header>
  );
}

import Link from "next/link";

import { Container } from "@/design-system/primitives/Container";
import { Wordmark } from "@/design-system/primitives/Wordmark";
import { routes } from "@/config/routes";

/**
 * The site footer, and the FOR SUPPLIERS column is the point of it.
 *
 * This is the agreed route into the portal: a supplier arrives on the
 * public site, finds "For suppliers" here, and from there can sign up or
 * sign in. The header carries the same path for anyone who looks up
 * rather than down, but the footer is where a visitor who has read the
 * page ends up, so the column is given real estate.
 *
 * The footer is also where the site's secondary navigation lives in
 * full -- About, Contact and the legal pages -- since the header stays
 * deliberately thin.
 */

const SUPPLIER_LINKS = [
  { href: routes.suppliers, label: "Why TruConnect", strong: false },
  { href: routes.signUp, label: "Create a supplier account", strong: true },
  { href: routes.signIn, label: "Supplier sign in", strong: false },
];

const COMPANY_LINKS = [
  { href: routes.about, label: "About" },
  { href: routes.contact, label: "Contact" },
  { href: routes.terms, label: "Terms of Service" },
  { href: routes.privacy, label: "Privacy Policy" },
];

export function SiteFooter() {
  return (
    <footer className="mt-auto border-t border-line/60 bg-wash">
      <Container className="py-14">
        <div className="grid gap-10 sm:grid-cols-2 lg:grid-cols-4">
          <div className="lg:col-span-2">
            <Wordmark className="text-lg" />
            <p className="mt-3 max-w-xs text-sm leading-relaxed text-ink-muted">
              The supply network for South Africa&rsquo;s independent businesses.
            </p>
          </div>

          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-ink">
              For suppliers
            </h2>
            <ul className="mt-4 space-y-2.5 text-sm">
              {SUPPLIER_LINKS.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className={
                      link.strong
                        ? "font-semibold text-brand-blue transition-colors hover:text-brand-green"
                        : "text-ink-muted transition-colors hover:text-brand-blue"
                    }
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <h2 className="text-xs font-bold uppercase tracking-wider text-ink">
              Company
            </h2>
            <ul className="mt-4 space-y-2.5 text-sm">
              {COMPANY_LINKS.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="text-ink-muted transition-colors hover:text-brand-blue"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
              <li className="text-ink-muted">Get the app &mdash; coming soon</li>
            </ul>
          </div>
        </div>

        <div className="mt-12 flex flex-col gap-3 border-t border-line/60 pt-6 text-xs text-ink-muted sm:flex-row sm:items-center sm:justify-between">
          <p>
            &copy; {new Date().getFullYear()} TruConnect. A TruePoint platform.
          </p>
          <p>Built in South Africa.</p>
        </div>
      </Container>
    </footer>
  );
}

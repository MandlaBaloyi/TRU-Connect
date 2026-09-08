"use client";

import Link from "next/link";
import { useState } from "react";

import { Logo } from "@/design-system/primitives/Logo";
import { routes } from "@/config/routes";

/**
 * The public site's top bar.
 *
 * TWO DOORS, NOT ONE, and that is the whole shape of it. A small trader
 * signs themselves up; a regional distributor wants to talk to a person
 * before moving a 3,000-line catalogue anywhere. A site with only a
 * "Sign up" button quietly tells the second one they are in the wrong
 * place -- which is the segment the business most needs.
 *
 * FLAT NAV, NO MEGA-MENU. Large platforms use dropdowns because they
 * have forty pages; this has six. A dropdown here would be a company
 * pretending to be bigger than it is, and it costs a tap on the phone
 * most of this audience is holding.
 *
 * NO BUSINESS SIGN-IN, deliberately. Businesses have no web surface --
 * their phone is with them all day and their problem does not require a
 * desk (V2_00 section 2.9). The app is their door and it is offered
 * further down the page, where there is room to say who it is for.
 */

const NAV = [
  { href: routes.suppliers, label: "For suppliers" },
  { href: routes.howItWorks, label: "How it works" },
  { href: routes.pricing, label: "Pricing" },
  { href: routes.about, label: "About" },
];

export function SiteHeader() {
  const [open, setOpen] = useState(false);

  return (
    <header className="sticky top-0 z-50 border-b border-line/60 bg-white/90 backdrop-blur-sm">
      <div className="mx-auto flex h-16 max-w-6xl items-center justify-between gap-4 px-5">
        <Link
          href={routes.home}
          className="shrink-0 rounded-sm focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-brand-blue"
          onClick={() => setOpen(false)}
        >
          <Logo className="text-xl" />
        </Link>

        <nav className="hidden items-center gap-1 lg:flex">
          {NAV.map((item) => (
            <Link
              key={item.href}
              href={item.href}
              className="rounded-md px-3 py-2 text-sm font-medium text-ink-muted transition-colors hover:text-ink"
            >
              {item.label}
            </Link>
          ))}
        </nav>

        <div className="hidden items-center gap-2 lg:flex">
          <Link
            href={routes.signIn}
            className="rounded-md px-3 py-2 text-sm font-medium text-ink-muted transition-colors hover:text-ink"
          >
            Sign in
          </Link>
          {/* THE SALES DOOR. Outlined rather than solid so it reads as
              equal to, not lesser than, self-serve -- a distributor and
              a trader are both wanted, they just arrive differently. */}
          <Link
            href={routes.contact}
            className="rounded-lg border border-brand-blue px-4 py-2 text-sm font-semibold text-brand-blue transition-colors hover:bg-brand-blue/5"
          >
            Contact sales
          </Link>
          <Link
            href={routes.signUp}
            className="rounded-lg bg-brand-blue px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-brand-blue-light focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-blue"
          >
            Get started
          </Link>
        </div>

        {/* MOBILE. A menu button rather than a squeezed row -- this
            audience is overwhelmingly on a phone, and four nav items
            plus three buttons does not fit at 360px however hard it is
            compressed. */}
        <button
          type="button"
          onClick={() => setOpen((value) => !value)}
          className="rounded-md p-2 text-ink lg:hidden"
          aria-expanded={open}
          aria-controls="site-menu"
          aria-label={open ? "Close menu" : "Open menu"}
        >
          <svg viewBox="0 0 24 24" className="h-6 w-6" fill="none" stroke="currentColor" strokeWidth="2">
            {open ? (
              <path d="M6 6l12 12M18 6L6 18" strokeLinecap="round" />
            ) : (
              <path d="M4 7h16M4 12h16M4 17h16" strokeLinecap="round" />
            )}
          </svg>
        </button>
      </div>

      {open && (
        <div id="site-menu" className="border-t border-line/60 bg-white px-5 py-4 lg:hidden">
          <nav className="flex flex-col gap-1">
            {NAV.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setOpen(false)}
                className="rounded-md px-2 py-3 text-base font-medium text-ink"
              >
                {item.label}
              </Link>
            ))}
          </nav>
          <div className="mt-4 flex flex-col gap-2 border-t border-line/60 pt-4">
            <Link
              href={routes.signIn}
              onClick={() => setOpen(false)}
              className="rounded-lg border border-line px-4 py-3 text-center text-base font-semibold text-ink"
            >
              Sign in
            </Link>
            <Link
              href={routes.contact}
              onClick={() => setOpen(false)}
              className="rounded-lg border border-brand-blue px-4 py-3 text-center text-base font-semibold text-brand-blue"
            >
              Contact sales
            </Link>
            <Link
              href={routes.signUp}
              onClick={() => setOpen(false)}
              className="rounded-lg bg-brand-blue px-4 py-3 text-center text-base font-semibold text-white"
            >
              Get started
            </Link>
          </div>
        </div>
      )}
    </header>
  );
}

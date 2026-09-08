"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Logo } from "@/design-system/primitives/Logo";
import { routes } from "@/config/routes";
import { signOut } from "@/domains/auth/services/authApi";

/**
 * The signed-in chrome: logo, and a way out.
 *
 * DELIBERATELY WITHOUT NAVIGATION. There is exactly one portal page
 * today, and a nav bar full of links to screens that do not exist would
 * be the sort of scaffolding that gets mistaken for progress -- which
 * is the thing surfaces/portal/README.md warns about in as many words.
 * Links arrive with the screens they point at.
 *
 * SIGN OUT IS THE ONE CONTROL THAT MUST BE HERE, because it is the
 * other half of the thing being tested: the cookie is httpOnly, so
 * clearing it is something only the server can do, and the button is
 * how you ask it to.
 */
export function PortalHeader() {
  const router = useRouter();
  const [busy, setBusy] = useState(false);

  async function handleSignOut() {
    setBusy(true);
    // signOut never throws -- see its own comment. Whatever happened
    // server-side, the person asked to leave, so they leave.
    await signOut();
    router.push(routes.signIn);
    // The next page must not read a stale client cache of the session.
    router.refresh();
  }

  return (
    <header className="border-b border-line/60 bg-white">
      <div className="mx-auto flex h-16 max-w-5xl items-center justify-between gap-4 px-5">
        <Logo className="text-xl" />
        <button
          type="button"
          onClick={handleSignOut}
          disabled={busy}
          className="rounded-md border border-line px-3.5 py-2 text-sm font-medium text-ink-muted transition-colors hover:border-ink-muted hover:text-ink disabled:opacity-60 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-blue"
        >
          {busy ? "Signing out…" : "Sign out"}
        </button>
      </div>
    </header>
  );
}

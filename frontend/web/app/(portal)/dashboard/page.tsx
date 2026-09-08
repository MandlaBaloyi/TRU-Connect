"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { PortalUser, session } from "@/domains/auth/services/authApi";
import { routes } from "@/config/routes";

/**
 * A SESSION PROBE, NOT A DASHBOARD.
 *
 * surfaces/portal/README.md says it outright -- "Not a dashboard. A
 * dashboard is the thing that feels like progress and is not" -- and
 * that still holds. The portal's real first screens are the catalogue
 * list and the CSV import, and they wait on the catalogue work.
 *
 * What this page exists for is narrower and immediate: until it
 * existed, a successful sign-in pushed to /dashboard and got a 404, so
 * the last step of the cookie-session flow could not be seen working.
 * It answers one question -- did the cookie survive the redirect and
 * does the backend recognise it -- and shows exactly what the backend
 * said, so a wrong answer is legible rather than just blank.
 *
 * It replaces itself the moment there is a real first screen to land
 * on.
 *
 * THE PROOF IS THAT THIS PAGE HOLDS NO CREDENTIAL. It receives no
 * token, reads no storage, and has nothing to pass along. It calls
 * session() and the browser attaches a cookie this code cannot see.
 * That is the whole design working.
 */
export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<PortalUser | null>(null);
  const [state, setState] = useState<"checking" | "in" | "out" | "error">("checking");
  const [message, setMessage] = useState<string | null>(null);

  useEffect(() => {
    // Guards against the request resolving after the component is gone
    // -- React mounts effects twice in development, and someone can
    // navigate away mid-request. A setState afterwards is a warning at
    // best and a stale render at worst.
    let cancelled = false;

    session()
      .then((found) => {
        if (cancelled) return;
        if (found) {
          setUser(found);
          setState("in");
        } else {
          setState("out");
          router.replace(routes.signIn);
        }
      })
      .catch((error: unknown) => {
        if (cancelled) return;
        // A backend that is down is NOT "signed out". Sending someone
        // to sign-in here would put them in a loop against a server
        // that cannot answer, so say what happened instead.
        setState("error");
        setMessage(error instanceof Error ? error.message : "Unknown error.");
      });

    return () => {
      cancelled = true;
    };
  }, [router]);

  if (state === "checking") {
    return <p className="text-ink-muted">Checking your session…</p>;
  }

  if (state === "error") {
    return (
      <div className="rounded-xl border border-amber-300 bg-amber-50 p-6">
        <h1 className="text-lg font-semibold text-amber-900">Could not reach TruConnect</h1>
        <p className="mt-2 text-sm text-amber-900/80">{message}</p>
        <p className="mt-4 text-sm text-amber-900/80">
          The backend is probably not running. Start it and reload.
        </p>
      </div>
    );
  }

  if (state === "out" || !user) {
    return <p className="text-ink-muted">Signed out. Taking you to sign in…</p>;
  }

  return (
    <div className="max-w-2xl">
      <div className="rounded-xl border border-brand-green/30 bg-brand-green/5 p-6">
        <p className="text-sm font-semibold uppercase tracking-wider text-brand-green-dark">
          Signed in
        </p>
        <h1 className="mt-2 text-2xl font-bold tracking-tight text-brand-blue">
          The cookie session works.
        </h1>
        <p className="mt-2 text-sm leading-relaxed text-ink-muted">
          This page asked the backend who you are and it answered. Nothing on this page holds a
          token — the credential is in a cookie your browser will not let JavaScript read.
        </p>
      </div>

      <dl className="mt-8 divide-y divide-line/70 rounded-xl border border-line/70 bg-white">
        {[
          ["Email", user.email],
          ["Role", user.role],
          ["Verification", user.verification_status],
          ["Account status", user.account_status],
          ["Last sign-in", user.last_login_at ?? "—"],
          ["User id", user.id],
        ].map(([label, value]) => (
          <div key={label} className="flex flex-wrap gap-2 px-5 py-3.5 text-sm">
            <dt className="w-40 shrink-0 font-medium text-ink-muted">{label}</dt>
            <dd className="min-w-0 break-all font-medium text-ink">{value}</dd>
          </div>
        ))}
      </dl>

      <p className="mt-8 text-sm leading-relaxed text-ink-muted">
        The real portal starts with the catalogue list and the CSV import. This page is here so the
        sign-in flow has somewhere to land, and it goes away when they arrive.
      </p>
    </div>
  );
}

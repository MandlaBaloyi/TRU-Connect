"use client";

import { useEffect, useRef, useState } from "react";

/**
 * Continue with Google.
 *
 * IT LOOKS LIVE AND TELLS YOU ON CLICK, rather than sitting there greyed
 * out under a "coming soon" caption. The caption version was honest and
 * bad: a permanently disabled control is dead weight on the page, it
 * reads as something broken rather than something planned, and it
 * explains an internal roadmap to a supplier who did not ask.
 *
 * The rule it still obeys is the one that matters -- NOBODY IS EVER LEFT
 * WONDERING WHAT HAPPENED. A button that silently does nothing is the
 * failure to avoid. Saying it when they reach for it costs them one tap
 * and tells them exactly as much as they need.
 *
 * THE MESSAGE IS A LIVE REGION, not just coloured text. A sighted user
 * sees it appear under their finger; a screen reader announces it. A
 * notice nobody is told about is the same as no notice.
 *
 * IT CLEARS ITSELF after a few seconds so a second attempt gets fresh
 * feedback rather than looking at a stale line -- and the timer is torn
 * down on unmount, because a setState after the component is gone is a
 * warning in development and a leak in a long session.
 *
 * WHEN THIS BECOMES REAL it is genuine backend work: provider
 * integration, account linking, and deciding what happens when a Google
 * address matches an existing password account. That is a project, not a
 * button, which is exactly why the button is not pretending otherwise.
 */
export function SocialSignIn({ action }: { action: "sign in" | "sign up" }) {
  const [notice, setNotice] = useState<string | null>(null);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => () => {
    if (timer.current) clearTimeout(timer.current);
  }, []);

  function handleClick() {
    setNotice(`Google ${action} is coming soon — use your email address for now.`);
    if (timer.current) clearTimeout(timer.current);
    timer.current = setTimeout(() => setNotice(null), 6000);
  }

  return (
    <div>
      <button
        type="button"
        onClick={handleClick}
        className="flex w-full items-center justify-center gap-3 rounded-lg border border-line bg-white px-4 py-3 text-base font-semibold text-ink shadow-sm transition-colors hover:border-ink-muted hover:bg-wash focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-blue"
      >
        <svg viewBox="0 0 24 24" className="h-5 w-5" aria-hidden>
          <path
            fill="#4285F4"
            d="M23.52 12.27c0-.85-.08-1.67-.22-2.45H12v4.63h6.46a5.52 5.52 0 0 1-2.4 3.62v3h3.87c2.26-2.09 3.59-5.17 3.59-8.8Z"
          />
          <path
            fill="#34A853"
            d="M12 24c3.24 0 5.96-1.08 7.94-2.91l-3.87-3.01c-1.08.72-2.45 1.15-4.07 1.15-3.13 0-5.78-2.11-6.73-4.95H1.28v3.11A12 12 0 0 0 12 24Z"
          />
          <path
            fill="#FBBC05"
            d="M5.27 14.28a7.2 7.2 0 0 1 0-4.56V6.61H1.28a12 12 0 0 0 0 10.78l3.99-3.11Z"
          />
          <path
            fill="#EA4335"
            d="M12 4.75c1.77 0 3.35.61 4.6 1.8l3.43-3.43C17.95 1.19 15.23 0 12 0A12 12 0 0 0 1.28 6.61l3.99 3.11C6.22 6.86 8.87 4.75 12 4.75Z"
          />
        </svg>
        Continue with Google
      </button>

      {/* Reserves no space when empty -- an always-present slot would
          reintroduce the caption this replaced. */}
      <div aria-live="polite" role="status">
        {notice && (
          <p className="mt-3 rounded-lg bg-brand-blue/5 px-3 py-2 text-center text-sm text-brand-blue">
            {notice}
          </p>
        )}
      </div>

      <div className="my-7 flex items-center gap-4">
        <span className="h-px flex-1 bg-line" />
        <span className="text-xs font-medium uppercase tracking-wider text-ink-muted">or</span>
        <span className="h-px flex-1 bg-line" />
      </div>
    </div>
  );
}

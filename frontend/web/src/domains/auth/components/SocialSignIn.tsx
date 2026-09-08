/**
 * Continue with Google — visible, and honestly disabled.
 *
 * THERE IS NO SOCIAL LOGIN ON THE BACKEND. Not a stub, not a
 * half-finished route: the auth domain contains no reference to Google,
 * OAuth or any provider at all. Building a button that silently did
 * nothing would be the same failure as a sign-in form that pretends to
 * log you in, and worse here, because a supplier who taps it and gets
 * nothing concludes the whole product is broken.
 *
 * SO IT IS SHOWN, AND IT SAYS SO. Disabled, greyed, with the reason on
 * it. That is a real pattern on real products and it costs nothing to be
 * straight about -- a supplier reads "coming soon" and uses their email,
 * which is what they were going to do anyway.
 *
 * The mark is inline SVG in Google's own brand colours rather than an
 * image: no network request, and no asset to keep in sync.
 *
 * WHEN IT BECOMES REAL it is a genuine piece of backend work -- provider
 * integration, account linking, and deciding what happens when a Google
 * address matches an existing password account. That is a project, not a
 * button.
 */
export function SocialSignIn({ action }: { action: "sign in" | "sign up" }) {
  return (
    <div>
      <button
        type="button"
        disabled
        aria-disabled
        title="Google sign-in is not available yet"
        className="flex w-full cursor-not-allowed items-center justify-center gap-3 rounded-lg border border-line bg-white px-4 py-3 text-base font-semibold text-ink-muted opacity-60"
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
      <p className="mt-2 text-center text-xs text-ink-muted">
        Google {action} is coming soon. Use your email address for now.
      </p>

      <div className="my-6 flex items-center gap-4">
        <span className="h-px flex-1 bg-line" />
        <span className="text-xs font-medium uppercase tracking-wider text-ink-muted">or</span>
        <span className="h-px flex-1 bg-line" />
      </div>
    </div>
  );
}

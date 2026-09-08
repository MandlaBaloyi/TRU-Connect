/**
 * The TruConnect wordmark: "Tru" in solid navy, "Connect" in italic
 * emerald.
 *
 * A typographic echo of the two-tone infinity logo, used INSTEAD of the
 * logo mark itself -- the same treatment the mobile app's brand top bar
 * uses (frontend/mobile/src/theme/wordmark.ts). Keeping the two
 * consistent matters more here than anywhere else on the site: this is
 * the one element a supplier will have already seen in the app.
 */
export function Wordmark({ className = "" }: { className?: string }) {
  return (
    <span
      className={`font-bold tracking-tight ${className}`}
      // The wordmark is one word to a screen reader, not two.
      aria-label="TruConnect"
    >
      <span aria-hidden className="text-brand-blue">
        Tru
      </span>
      <span aria-hidden className="italic text-brand-green">
        Connect
      </span>
    </span>
  );
}

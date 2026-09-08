/**
 * The TruConnect logo lockup: mark plus wordmark.
 *
 * THE MARK IS TWO INTERLOCKING LOOPS -- an infinity form, drawn as two
 * halves in the two brand colours. It is the shape the platform
 * constitution describes, and it says the one thing the product is
 * about: two sides that only work joined. A business alone is a shop
 * that cannot restock; a supplier alone is stock nobody can reach.
 *
 * INLINE SVG, NOT AN IMAGE FILE, and that is deliberate. It renders on
 * the first paint with no network request, scales to any size without a
 * second asset, and inherits the brand tokens -- so a colour change is
 * one edit here rather than a re-export. On a marketing page opened over
 * mobile data in South Africa, a logo that costs zero requests is worth
 * more than one that is pixel-perfect.
 *
 * `mark` renders the symbol alone, for a favicon-sized or square slot.
 */
export function Logo({
  className = "",
  markOnly = false,
}: {
  className?: string;
  markOnly?: boolean;
}) {
  return (
    <span className={`inline-flex items-center gap-2.5 ${className}`} aria-label="TruConnect">
      <svg
        viewBox="0 0 44 24"
        className="h-[1.15em] w-auto shrink-0"
        role="presentation"
        aria-hidden
        fill="none"
      >
        {/* Left loop -- navy. The business side. */}
        <path
          d="M22 12c0-5-3.6-9-8.5-9S5 7 5 12s3.6 9 8.5 9S22 17 22 12Z"
          stroke="var(--color-brand-blue)"
          strokeWidth="3.5"
          strokeLinecap="round"
        />
        {/* Right loop -- emerald. The supply side. They overlap at the
            centre on purpose: the join is the product. */}
        <path
          d="M22 12c0-5 3.6-9 8.5-9S39 7 39 12s-3.6 9-8.5 9S22 17 22 12Z"
          stroke="var(--color-brand-green)"
          strokeWidth="3.5"
          strokeLinecap="round"
        />
      </svg>

      {!markOnly && (
        <span className="font-bold tracking-tight">
          <span aria-hidden className="text-brand-blue">
            Tru
          </span>
          <span aria-hidden className="italic text-brand-green">
            Connect
          </span>
        </span>
      )}
    </span>
  );
}

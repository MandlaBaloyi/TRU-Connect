import type { ReactNode } from "react";

/**
 * A grid of short titled blocks -- the problem cards on the home page,
 * the "what you get" cards on the supplier page.
 *
 * `numbered` turns it into an ordered list with a step index, for the
 * "how it works" sequence. Same shape, one prop, so the two do not drift
 * apart visually.
 */

export type InfoCard = {
  title: string;
  body: ReactNode;
};

export function InfoCardGrid({
  heading,
  intro,
  cards,
  columns = 3,
  numbered = false,
}: {
  heading?: string;
  intro?: ReactNode;
  cards: InfoCard[];
  columns?: 2 | 3;
  numbered?: boolean;
}) {
  const cols = columns === 2 ? "md:grid-cols-2" : "md:grid-cols-3";

  return (
    <div>
      {heading && (
        <h2 className="max-w-2xl text-balance text-3xl font-bold tracking-tight text-brand-blue sm:text-4xl">
          {heading}
        </h2>
      )}
      {intro && (
        <p className="mt-4 max-w-2xl text-lg leading-relaxed text-ink-muted">
          {intro}
        </p>
      )}

      {numbered ? (
        <ol className={`mt-12 grid gap-8 ${cols}`}>
          {cards.map((card, i) => (
            <li key={card.title}>
              <span className="text-sm font-bold tracking-wider text-brand-green">
                {String(i + 1).padStart(2, "0")}
              </span>
              <h3 className="mt-3 text-lg font-semibold text-ink">
                {card.title}
              </h3>
              <p className="mt-2 text-sm leading-relaxed text-ink-muted">
                {card.body}
              </p>
            </li>
          ))}
        </ol>
      ) : (
        <div className={`mt-12 grid gap-6 ${cols}`}>
          {cards.map((card) => (
            <div
              key={card.title}
              className="rounded-2xl bg-white p-6 shadow-sm ring-1 ring-line/60 transition-shadow hover:shadow-md"
            >
              <h3 className="text-lg font-semibold text-brand-blue">
                {card.title}
              </h3>
              <p className="mt-3 text-sm leading-relaxed text-ink-muted">
                {card.body}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

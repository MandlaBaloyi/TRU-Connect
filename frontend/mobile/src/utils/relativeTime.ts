/**
 * Relative time: what to say, and WHEN what we said stops being true.
 *
 * formatWhen moved here from components/lists/CardListUI.tsx (which
 * still re-exports it, so nothing broke). A hook should not import a
 * formatter out of a components file, and the second function below is
 * the reason there now is a hook.
 *
 * NO "WEEKS" STEP, deliberately, though V2_04 2.3's prose says "last
 * ordered 3 weeks ago". Days are what this line is FOR: a shopkeeper
 * deciding whether a supplier is due reads "19 days ago" and knows;
 * "3 weeks ago" rounds away the difference between 15 days and 21,
 * which is exactly the difference the reorder gap is measuring. The
 * doc's phrasing is illustrative prose, not a contract -- and adding
 * the step would change every relative time in the app, not this one
 * line.
 */

const SECOND = 1000;
const MINUTE = 60 * SECOND;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;
const MONTH = 30 * DAY;
const YEAR = 12 * MONTH;

/** Friendly relative time — no raw timestamps in the UI. */
export function formatWhen(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / MINUTE);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins} minute${mins === 1 ? "" : "s"} ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} day${days === 1 ? "" : "s"} ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months} month${months === 1 ? "" : "s"} ago`;
  const years = Math.floor(months / 12);
  return `${years} year${years === 1 ? "" : "s"} ago`;
}

/**
 * The epoch millisecond at which formatWhen(iso) would return something
 * DIFFERENT from what it returns now.
 *
 * THIS IS WHAT MAKES A LIVE CLOCK CHEAP. The alternative — waking every
 * thirty seconds and re-rendering everything — burns work on rows whose
 * text cannot possibly have changed: "21 days ago" is true for a full
 * day. Because formatWhen is a ladder of whole units, the moment each
 * label turns over is COMPUTABLE, so the clock can sleep exactly that
 * long and no longer.
 *
 * A screen of week-old orders therefore schedules a wake-up hours away
 * and costs nothing; a screen with a thirty-second-old order ticks in
 * thirty seconds. The cost tracks how fresh the data is, which is the
 * only thing it should track.
 */
export function nextChangeAt(iso: string): number {
  const seen = new Date(iso).getTime();
  if (Number.isNaN(seen)) return Number.POSITIVE_INFINITY;

  const age = Date.now() - seen;
  // Which rung are we on, and when does the next whole unit tick over?
  if (age < MINUTE) return seen + MINUTE;
  if (age < HOUR) return seen + (Math.floor(age / MINUTE) + 1) * MINUTE;
  if (age < DAY) return seen + (Math.floor(age / HOUR) + 1) * HOUR;
  if (age < MONTH) return seen + (Math.floor(age / DAY) + 1) * DAY;
  if (age < YEAR) return seen + (Math.floor(age / MONTH) + 1) * MONTH;
  return seen + (Math.floor(age / YEAR) + 1) * YEAR;
}

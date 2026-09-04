/**
 * A small, dedicated relative-time formatter -- no date-fns dependency
 * added for one function; this is the entire real requirement
 * (notification timestamps), not a general-purpose date library.
 *
 * "Just now" / "5m" / "3h" / "Yesterday" / "3 Sep" -- matches the same
 * bank-SMS brevity instinct the notification message bodies
 * themselves were built around: a glance should be enough.
 */
export function formatRelativeTime(iso: string): string {
  const then = new Date(iso).getTime();
  const now = Date.now();
  const diffMs = now - then;
  const diffMinutes = Math.floor(diffMs / 60000);

  if (diffMinutes < 1) return "Just now";
  if (diffMinutes < 60) return `${diffMinutes}m`;

  const diffHours = Math.floor(diffMinutes / 60);
  if (diffHours < 24) return `${diffHours}h`;

  const thenDate = new Date(iso);
  const nowDate = new Date();
  // Midnight-normalized comparison, not raw getDate() subtraction --
  // a real bug caught before shipping: getDate()-1 breaks at month
  // boundaries (today being the 1st makes getDate()-1 equal 0, which
  // never matches any real date). Comparing whole calendar days via
  // their own midnight timestamps is correct at every boundary.
  const startOfToday = new Date(nowDate.getFullYear(), nowDate.getMonth(), nowDate.getDate()).getTime();
  const startOfThen = new Date(thenDate.getFullYear(), thenDate.getMonth(), thenDate.getDate()).getTime();
  const calendarDaysAgo = Math.round((startOfToday - startOfThen) / 86400000);
  if (calendarDaysAgo === 1) return "Yesterday";

  const diffDays = Math.floor(diffHours / 24);
  if (diffDays < 7) return `${diffDays}d`;

  return thenDate.toLocaleDateString(undefined, { day: "numeric", month: "short" });
}

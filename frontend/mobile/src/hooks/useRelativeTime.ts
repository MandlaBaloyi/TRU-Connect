import { useEffect, useState } from "react";
import { AppState } from "react-native";

import { formatWhen, nextChangeAt } from "@/utils/relativeTime";

/**
 * A relative timestamp that stays true while you look at it.
 *
 * THE PROBLEM IT SOLVES IS CORRECTNESS, NOT POLISH. formatWhen is
 * computed at render, so a row rendered an hour ago still claims "6
 * hours ago" when the truth is seven — and after the phone has been
 * asleep it can be wrong by however long the nap was. Nothing forces a
 * re-render, so the number simply rots on screen. That is a quiet lie,
 * and the fact that nobody has complained is not evidence it is fine.
 *
 * THE NAIVE FIXES ARE WHY THIS IS A MODULE AND NOT A setInterval.
 * A timer per row means fifty timers and fifty re-renders a minute; a
 * timer in the list re-renders every row even when not one label
 * changed. Both are wasteful AND sloppy, which is the same objection
 * twice.
 *
 * SO: ONE CLOCK, WOKEN ONLY WHEN A LABEL ACTUALLY TURNS OVER.
 *
 *   1  Every subscriber registers the instant its own text next
 *      changes (nextChangeAt — a ladder of whole units, so the moment
 *      is knowable, not guessed).
 *   2  The clock keeps ONE timeout, set to the soonest of those.
 *      A screen of week-old rows sleeps for hours.
 *   3  A woken subscriber re-renders only if its STRING differs.
 *      Ticking is not repainting.
 *   4  AppState resumption recomputes everything at once, which is the
 *      case the current code gets wrong rather than merely slowly.
 *
 * Nothing here is per-component state, so a hundred rows cost one
 * timer.
 */

type Subscriber = () => void;

/** Each subscriber against the epoch ms at which it wants waking. */
const dueAt = new Map<Subscriber, number>();
let timer: ReturnType<typeof setTimeout> | null = null;

function reschedule(): void {
  if (timer) {
    clearTimeout(timer);
    timer = null;
  }
  if (dueAt.size === 0) return;

  let soonest = Number.POSITIVE_INFINITY;
  for (const due of dueAt.values()) soonest = Math.min(soonest, due);
  if (!Number.isFinite(soonest)) return;

  // A floor keeps a pathological timestamp (clock skew, a future date)
  // from becoming a busy loop.
  const delay = Math.max(250, soonest - Date.now());
  timer = setTimeout(fire, delay);
}

function fire(): void {
  timer = null;
  const now = Date.now();
  // Snapshot: a subscriber re-registers itself as it runs, and mutating
  // the map mid-iteration is how that turns into a missed wake-up.
  for (const [subscriber, due] of Array.from(dueAt.entries())) {
    if (due <= now) subscriber();
  }
  reschedule();
}

// COMING BACK FROM THE BACKGROUND IS THE IMPORTANT CASE. Timers do not
// reliably fire while suspended, so on resume every label is recomputed
// rather than waiting for a timeout that may never have run.
AppState.addEventListener("change", (state) => {
  if (state !== "active") return;
  for (const subscriber of Array.from(dueAt.keys())) subscriber();
  reschedule();
});

export function useRelativeTime(iso: string | null | undefined): string | null {
  const [label, setLabel] = useState<string | null>(() => (iso ? formatWhen(iso) : null));

  useEffect(() => {
    if (!iso) {
      setLabel(null);
      return;
    }

    // Recompute immediately: the value may have aged between the last
    // render and this effect, and on remount the initial state was
    // computed from a possibly-stale prop.
    const tick = () => {
      const next = formatWhen(iso);
      dueAt.set(tick, nextChangeAt(iso));
      // Identical string means React bails out and NOTHING re-renders.
      setLabel((prev) => (prev === next ? prev : next));
    };

    tick();
    reschedule();

    return () => {
      dueAt.delete(tick);
      reschedule();
    };
  }, [iso]);

  return label;
}

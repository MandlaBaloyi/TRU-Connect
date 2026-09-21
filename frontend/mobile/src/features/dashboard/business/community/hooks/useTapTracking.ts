import { useCallback, useEffect, useRef } from "react";
import { AppState } from "react-native";

import {
  MAX_TAPS_PER_REQUEST,
  sendTaps,
  type FeedTap,
} from "../services/impressionService";

/**
 * Collecting taps on the feed and sending them in batches.
 *
 * WHY A BUFFER AND NOT ONE POST PER TAP. The endpoint is rate limited
 * per minute, deliberately and from day one — it is the only write in
 * this domain a device can drive on a timer. A shopkeeper scrolling
 * hard would trip that limit on their own feed within seconds if every
 * tap were its own request, and the first thing they would notice is
 * their own app failing.
 *
 * THREE THINGS FLUSH IT, and the third is the one that matters most:
 *
 *   FULL      MAX_TAPS_PER_REQUEST reached — send now rather than
 *             quietly dropping the overflow.
 *   TIMER     FLUSH_AFTER_MS of quiet, so a short visit still counts.
 *   LEAVING   the app going to background, and unmount. Without this
 *             the most engaged session — open the tab, tap through to
 *             a supplier, never come back — is the session that
 *             reports nothing, and the data would be biased towards
 *             exactly the behaviour we care least about.
 *
 * THE BUFFER IS A REF, NOT STATE. Nothing renders from it, and making
 * it state would re-render the whole feed on every tap — a measurable
 * cost paid for an invisible benefit.
 */

/** Quiet period before an unsent batch goes. Short enough that a
 *  30-second visit is recorded, long enough that a burst of taps is
 *  one request. */
const FLUSH_AFTER_MS = 5000;

export function useTapTracking() {
  const buffer = useRef<FeedTap[]>([]);
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const flush = useCallback(() => {
    if (timer.current) {
      clearTimeout(timer.current);
      timer.current = null;
    }
    if (buffer.current.length === 0) return;

    // TAKEN BEFORE SENDING, so taps arriving during an in-flight
    // request join the NEXT batch instead of being cleared with this
    // one. The bug this avoids is silent and only shows up under a
    // fast finger.
    const batch = buffer.current;
    buffer.current = [];
    void sendTaps(batch);
  }, []);

  const reportTap = useCallback(
    (tap: FeedTap) => {
      buffer.current.push(tap);

      if (buffer.current.length >= MAX_TAPS_PER_REQUEST) {
        flush();
        return;
      }
      if (timer.current) clearTimeout(timer.current);
      timer.current = setTimeout(flush, FLUSH_AFTER_MS);
    },
    [flush]
  );

  useEffect(() => {
    const subscription = AppState.addEventListener("change", (state) => {
      // BACKGROUND *AND* INACTIVE. iOS passes through "inactive" on the
      // way out, and on some transitions that is the last callback the
      // app gets — treating only "background" as leaving loses those.
      if (state === "background" || state === "inactive") flush();
    });

    return () => {
      subscription.remove();
      flush();
    };
  }, [flush]);

  return { reportTap, flush };
}

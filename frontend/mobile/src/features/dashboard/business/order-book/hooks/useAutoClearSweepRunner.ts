/**
 * useAutoClearSweepRunner — runs the auto-clear check.
 *
 * Waits for useAutoClearSettings to finish its initial load before
 * running a sweep, then re-checks every 30s while this screen is
 * mounted — since a duration as short as 5 minutes needs more than a
 * single check on app open to ever actually fire during a session.
 *
 * STILL NEEDED EVEN AGAINST THE REAL BACKEND: the backend's sweep
 * (AutoClearService.run_sweep) exists and is correct, but nothing on
 * the server calls it on a timer yet — see
 * backend/.../services/auto_clear_service.py's own docstring. This
 * hook is what actually triggers it today, by calling the manual
 * POST /order-book/balances/auto-clear-sweep endpoint periodically
 * from the client. Once a real scheduled job exists server-side, this
 * hook becomes redundant (harmless to leave running, but no longer
 * load-bearing) rather than something that needs deleting.
 */

import { useEffect, useRef } from "react";
import { useQueryClient } from "@tanstack/react-query";

import { runAutoClearSweep } from "../api/orderBookApi";
import { orderBookKeys } from "./orderBookKeys";
import { useAutoClearSettings } from "./useAutoClearSettings";
import { useCurrentUserId } from "./useCurrentUserId";

const CHECK_INTERVAL_MS = 30 * 1000;

export function useAutoClearSweepRunner() {
  const userId = useCurrentUserId();
  const queryClient = useQueryClient();
  const { isLoading: isDurationLoading } = useAutoClearSettings();
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  useEffect(() => {
    if (isDurationLoading || !userId) return;

    const runSweep = async () => {
      const result = await runAutoClearSweep();
      if (result.clearedCount > 0) {
        queryClient.invalidateQueries({ queryKey: orderBookKeys.all(userId) });
      }
    };

    runSweep();
    intervalRef.current = setInterval(runSweep, CHECK_INTERVAL_MS);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isDurationLoading, userId, queryClient]);
}

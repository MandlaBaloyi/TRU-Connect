/**
 * useAutoClearSettings — completed and cancelled auto-clear settings.
 *
 * LOADS VIA GET, SAVES VIA PUT — nothing else. Earlier this hook read a
 * locally-cached copy from AsyncStorage on mount and immediately wrote
 * it back to the backend as a "sync" step. That made sense back when
 * the mock API was the only backend and its in-memory state reset on
 * every reload — pushing the cached value back in was how mock mode
 * kept the setting alive across restarts. Against a REAL backend this
 * was actively wrong: the backend is now the actual source of truth,
 * so treating a load as an occasion to also write is a bug, not a
 * feature — every mount of a screen that used this hook (the Order
 * Book queue, via useAutoClearSweepRunner, AND the Balances screen)
 * fired a PUT that had nothing to do with the user changing anything.
 * Confirmed in production logs: dozens of PUT .../auto-clear-settings
 * calls with no corresponding user action.
 *
 * Now: mount -> one GET, done. A write only ever happens when
 * setSetting() is called, which only the "Set" button and the preset
 * chips do. No AsyncStorage, no client-side cache to keep in sync —
 * the backend already persists this per business, which is exactly
 * what AsyncStorage was standing in for before a backend existed.
 */

import { useCallback, useEffect, useState } from "react";

import type { AutoClearScope, AutoClearSetting } from "../types";
import { getAutoClearSettings, setAutoClearSetting } from "../api/orderBookApi";

const DEFAULT_SETTING: AutoClearSetting = { duration: "OFF" };

export function useAutoClearSettings() {
  const [completedSetting, setCompletedSettingState] = useState<AutoClearSetting>(DEFAULT_SETTING);
  const [cancelledSetting, setCancelledSettingState] = useState<AutoClearSetting>(DEFAULT_SETTING);
  const [isLoading, setIsLoading] = useState(true);
  const [loadError, setLoadError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getAutoClearSettings()
      .then((settings) => {
        if (cancelled) return;
        setCompletedSettingState(settings.completed);
        setCancelledSettingState(settings.cancelled);
      })
      .catch((error) => {
        if (cancelled) return;
        // Falls back to OFF/OFF rather than blocking the screen — the
        // accordion still renders, it just starts from a safe default
        // until the next successful load.
        setLoadError(error instanceof Error ? error.message : "Could not load auto-clear settings.");
      })
      .finally(() => {
        if (!cancelled) setIsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const setSetting = useCallback(async (scope: AutoClearScope, next: AutoClearSetting) => {
    const saved = await setAutoClearSetting(scope, next);
    if (scope === "COMPLETED") {
      setCompletedSettingState(saved);
    } else {
      setCancelledSettingState(saved);
    }
    return saved;
  }, []);

  return { completedSetting, cancelledSetting, setSetting, isLoading, loadError };
}

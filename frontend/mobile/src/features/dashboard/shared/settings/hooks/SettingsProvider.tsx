/**
 * App-wide settings context.
 *
 * MOUNTED ABOVE ThemeProvider in app/_layout.tsx on purpose: the Theme
 * setting has to reach EVERY screen (Home, Account, Loan Book, Order
 * Book, Community, Discovery, More), not just the Settings screen
 * itself. A settings store living inside the Settings feature's own
 * screen could never do that — which is why this provider sits at the
 * app root even though the feature folder it belongs to is
 * business/settings.
 */
import React, { createContext, useCallback, useContext, useEffect, useMemo, useState } from "react";

import { AppSettings, DEFAULT_SETTINGS } from "../types";
import { loadSettings, saveSettings } from "../services/settingsStorage";

interface SettingsContextValue {
  settings: AppSettings;
  /** Partial update — callers change one key without having to
   *  reconstruct the whole object (and without risking clobbering a
   *  setting they weren't editing). Persists immediately. */
  updateSettings: (patch: Partial<AppSettings>) => void;
  /** False until the stored preferences have actually been read.
   *  ThemeProvider uses this to avoid a visible flash of the wrong
   *  theme on cold start. */
  isLoaded: boolean;
}

const SettingsContext = createContext<SettingsContextValue>({
  settings: DEFAULT_SETTINGS,
  updateSettings: () => {},
  isLoaded: false,
});

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const [settings, setSettings] = useState<AppSettings>(DEFAULT_SETTINGS);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    loadSettings().then((loaded) => {
      if (cancelled) return;
      setSettings(loaded);
      setIsLoaded(true);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  const updateSettings = useCallback((patch: Partial<AppSettings>) => {
    setSettings((current) => {
      const next = { ...current, ...patch };
      // Fire-and-forget: the UI already reflects the new value from
      // state, so waiting on the write would only add latency.
      void saveSettings(next);
      return next;
    });
  }, []);

  const value = useMemo(
    () => ({ settings, updateSettings, isLoaded }),
    [settings, updateSettings, isLoaded]
  );

  return <SettingsContext.Provider value={value}>{children}</SettingsContext.Provider>;
}

export function useSettings(): SettingsContextValue {
  return useContext(SettingsContext);
}

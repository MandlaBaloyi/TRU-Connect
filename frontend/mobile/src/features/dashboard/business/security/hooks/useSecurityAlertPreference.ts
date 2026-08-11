/**
 * Security alert notification preference — REAL, not a fake switch.
 *
 * Persists to AsyncStorage the same way settingsStorage.ts does (see
 * that file for the pattern this mirrors). DEFAULT IS OFF, per direct
 * instruction: the user has to actively turn this on.
 *
 * WHAT THIS TOGGLE ACTUALLY CONTROLS: whether TruConnect notifies you
 * about security alerts outside the app (push/SMS, once that
 * infrastructure exists). It does NOT hide alerts from this screen
 * either way — alerts that already happened (like a blocked sign-in
 * attempt) are always visible here regardless of this setting, because
 * hiding a real security event from the one screen that shows it would
 * be actively harmful. This preference is genuinely persisted today;
 * only the OUTSIDE-the-app notification delivery is pending backend
 * infrastructure, same category as every other "coming soon" piece in
 * this app.
 */
import AsyncStorage from "@react-native-async-storage/async-storage";
import { useCallback, useEffect, useState } from "react";

const STORAGE_KEY = "truconnect.security.alertsEnabled.v1";
const DEFAULT_ENABLED = false;

export function useSecurityAlertPreference() {
  const [isEnabled, setIsEnabled] = useState(DEFAULT_ENABLED);
  const [isLoaded, setIsLoaded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    AsyncStorage.getItem(STORAGE_KEY)
      .then((raw) => {
        if (cancelled) return;
        setIsEnabled(raw === null ? DEFAULT_ENABLED : raw === "true");
        setIsLoaded(true);
      })
      .catch(() => {
        if (!cancelled) setIsLoaded(true); // fall back to the default, never block the screen
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const setEnabled = useCallback((next: boolean) => {
    setIsEnabled(next);
    AsyncStorage.setItem(STORAGE_KEY, String(next)).catch(() => {
      // Persistence failing isn't worth interrupting the user over --
      // the in-memory value still applies for this session.
    });
  }, []);

  return { isEnabled, isLoaded, setEnabled };
}

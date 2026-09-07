/**
 * Settings persistence. AsyncStorage, NOT secureStorage — these are
 * device preferences (theme, language, start screen), not credentials.
 * secureStorage is reserved for tokens; putting non-sensitive
 * preferences behind the secure keystore would be slower for no
 * security benefit.
 *
 * Deliberately survives sign-out: theme and language are properties of
 * how this PERSON uses this DEVICE, not of the business session. A
 * shop owner who set dark mode shouldn't have it silently reset the
 * next time they log in.
 */
import AsyncStorage from "@react-native-async-storage/async-storage";

import { AppSettings, DEFAULT_SETTINGS } from "../types";

const STORAGE_KEY = "truconnect.settings.v1";

export async function loadSettings(): Promise<AppSettings> {
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY);
    if (!raw) return DEFAULT_SETTINGS;
    const parsed = JSON.parse(raw) as Partial<AppSettings>;
    // Merged over defaults rather than used directly: a build that adds
    // a new setting must not crash on values written by an older build
    // that never knew about it.
    return { ...DEFAULT_SETTINGS, ...parsed };
  } catch {
    // A corrupt/unreadable preferences blob must never block the app
    // from starting — fall back to defaults silently.
    return DEFAULT_SETTINGS;
  }
}

export async function saveSettings(settings: AppSettings): Promise<void> {
  try {
    await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
  } catch {
    // Persisting preferences failing is not worth interrupting the user
    // over — the in-memory value still applies for this session.
  }
}

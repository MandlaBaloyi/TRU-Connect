/**
 * Biometric capability + enable/disable, wrapping
 * expo-local-authentication.
 *
 * REAL DEVICE CAPABILITY, NOT MOCKED — unlike the rest of this
 * feature (which is mock-backed pending a backend), biometrics are a
 * genuinely device-local concern with a real Expo API, so this is
 * wired to the actual hardware from day one. We never implement
 * biometric matching ourselves; the OS prompt does it.
 *
 * THREE DISTINCT STATES, deliberately not collapsed into one boolean,
 * because each needs different copy and a different call to action:
 *   isAvailable  — does the device have the hardware at all?
 *   isEnrolled   — has the user actually registered a fingerprint/face
 *                  IN THE OS? Hardware can exist with nothing enrolled,
 *                  in which case the fix is in device settings, not
 *                  in TruConnect.
 *   isEnabledForApp — has the user chosen to use it for TruConnect?
 */
import { useCallback, useEffect, useState } from "react";
import * as LocalAuthentication from "expo-local-authentication";

import type { BiometricKind } from "../types";
import { getBiometricEnabledForApp, setBiometricEnabledForApp } from "../services/securityService";

interface BiometricsState {
  isAvailable: boolean;
  isEnrolled: boolean;
  kind: BiometricKind;
  isEnabledForApp: boolean;
  isLoading: boolean;
}

function resolveKind(types: LocalAuthentication.AuthenticationType[]): BiometricKind {
  if (types.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION)) return "FACE";
  if (types.includes(LocalAuthentication.AuthenticationType.FINGERPRINT)) return "FINGERPRINT";
  if (types.includes(LocalAuthentication.AuthenticationType.IRIS)) return "IRIS";
  return "NONE";
}

export function useBiometrics() {
  const [state, setState] = useState<BiometricsState>({
    isAvailable: false,
    isEnrolled: false,
    kind: "NONE",
    isEnabledForApp: getBiometricEnabledForApp(),
    isLoading: true,
  });

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const [isAvailable, isEnrolled, types] = await Promise.all([
          LocalAuthentication.hasHardwareAsync(),
          LocalAuthentication.isEnrolledAsync(),
          LocalAuthentication.supportedAuthenticationTypesAsync(),
        ]);
        if (cancelled) return;
        setState((s) => ({ ...s, isAvailable, isEnrolled, kind: resolveKind(types), isLoading: false }));
      } catch {
        // A capability check failing must never block the screen --
        // fall back to "not available", which renders honest copy
        // rather than an error.
        if (!cancelled) setState((s) => ({ ...s, isLoading: false }));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  /**
   * Turning biometrics ON requires passing the OS prompt FIRST — you
   * should never be able to enable a lock you can't actually open.
   * Turning it OFF requires no prompt: locking someone out of
   * disabling a feature would violate the spec's rule that biometrics
   * must never permanently lock a user out.
   */
  const setEnabled = useCallback(async (next: boolean): Promise<boolean> => {
    if (!next) {
      setBiometricEnabledForApp(false);
      setState((s) => ({ ...s, isEnabledForApp: false }));
      return true;
    }

    const result = await LocalAuthentication.authenticateAsync({
      promptMessage: "Confirm it's you to turn on biometric sign-in",
      // Always leave a way through that isn't biometrics, so a failed
      // fingerprint can never strand the user (spec §18.13).
      disableDeviceFallback: false,
    });

    if (result.success) {
      setBiometricEnabledForApp(true);
      setState((s) => ({ ...s, isEnabledForApp: true }));
      return true;
    }
    return false;
  }, []);

  return { ...state, setEnabled };
}

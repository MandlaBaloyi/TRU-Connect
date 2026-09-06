import { initialWindowMetrics, useSafeAreaInsets } from "react-native-safe-area-context";

/**
 * The REAL, WINDOW-LEVEL safe-area insets -- immune to nested
 * SafeAreaProviders.
 *
 * THE BUG THIS EXISTS TO FIX, diagnosed from real device logs rather
 * than assumed. After the SDK 54 -> 57 upgrade, a black strip appeared
 * behind the status bar on every screen. useSafeAreaInsets() was
 * returning {top:0,bottom:0,left:0,right:0} inside AppHeader, on a
 * device that simultaneously reported StatusBar.currentHeight of
 * 23.47 and a root initialWindowMetrics of
 * {top: 23.47, bottom: 14.93} -- correct values at the root, zeros
 * one level down.
 *
 * WHY: useSafeAreaInsets() resolves to the NEAREST SafeAreaProvider,
 * not the root one. react-native-screens 4.26 (new in SDK 57) wraps
 * each screen in its OWN nested SafeAreaProvider. Logging
 * useSafeAreaFrame() alongside the insets proved it conclusively: the
 * frame AppHeader sees starts at y=23.47 (exactly the status bar
 * height) with height 817.78, versus the root's y=0 / height 856.18 --
 * and 856.18 - 23.47 - 14.93 = 817.78 exactly. So the nested provider
 * genuinely begins BELOW the status bar, meaning top:0 is the correct
 * answer *for that provider*. It's not broken; it's a different
 * coordinate space than the one this app's chrome needs.
 *
 * On SDK 54's older react-native-screens that nested provider didn't
 * exist, so the same hook resolved to the root and returned real
 * values -- which is why this only broke on upgrade despite no
 * app-code change.
 *
 * WHY THIS APP NEEDS THE ROOT VALUE SPECIFICALLY: AppHeader and the
 * bottom tab bar deliberately extend edge-to-edge, painting their own
 * background behind the system bars (see AppHeader's own docstring on
 * why it owns that region rather than delegating to an outer
 * SafeAreaView). That only works with the WINDOW's insets. A screen
 * rendering ordinary content inside the safe area should keep using
 * useSafeAreaInsets() normally -- this hook is specifically for the
 * chrome that intentionally sits underneath the system bars.
 *
 * initialWindowMetrics is read once natively at module load, at the
 * window level, before any nesting exists -- so it's a genuine root
 * measurement, not a workaround value. The live hook is still
 * preferred whenever it returns something real (it accounts for
 * runtime changes like rotation that a load-time constant can't); the
 * root metrics only fill in when the nearest provider reports zero.
 */
export function useRootSafeAreaInsets() {
  const nearest = useSafeAreaInsets();
  const root = initialWindowMetrics?.insets;

  if (!root) return nearest;

  return {
    top: nearest.top || root.top,
    bottom: nearest.bottom || root.bottom,
    left: nearest.left || root.left,
    right: nearest.right || root.right,
  };
}

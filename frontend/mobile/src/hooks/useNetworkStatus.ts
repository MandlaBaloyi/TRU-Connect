import { useEffect, useState } from "react";
import { Platform } from "react-native";

/**
 * Minimal connectivity hook backing <OfflineBanner />.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (UX Requirements --
 * Offline States).
 *
 * NOTE: this uses `navigator.onLine` on web, which is accurate, and
 * defaults to `true` (assume online) on native platforms, since a native
 * connectivity API (e.g. @react-native-community/netinfo) is not part of
 * the approved dependency list for this phase. When native connectivity
 * detection is required, add that package explicitly and swap the native
 * branch below -- do not substitute a different library ad hoc.
 */
export function useNetworkStatus(): { isOffline: boolean } {
  const [isOffline, setIsOffline] = useState(false);

  useEffect(() => {
    if (Platform.OS !== "web" || typeof navigator === "undefined") {
      return;
    }
    const updateStatus = () => setIsOffline(!navigator.onLine);
    updateStatus();
    window.addEventListener("online", updateStatus);
    window.addEventListener("offline", updateStatus);
    return () => {
      window.removeEventListener("online", updateStatus);
      window.removeEventListener("offline", updateStatus);
    };
  }, []);

  return { isOffline };
}

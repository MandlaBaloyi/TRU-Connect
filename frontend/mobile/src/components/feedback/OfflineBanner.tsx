import React from "react";
import { StyleSheet, View } from "react-native";
import { Text } from "react-native-paper";
import { WifiOff } from "lucide-react-native";
import { useNetworkStatus } from "@/hooks/useNetworkStatus";
import { palette } from "@/theme/colors";
import { spacing } from "@/theme/spacing";

/**
 * Slim banner shown at the top of the app when offline. Mounted once in
 * app/_layout.tsx so it is visible across every screen.
 * Ref: master prompt "REUSABLE COMPONENTS" (OfflineBanner) and "USER
 * EXPERIENCE" (Offline States).
 */
export function OfflineBanner() {
  const { isOffline } = useNetworkStatus();
  if (!isOffline) return null;

  return (
    <View style={styles.banner}>
      <WifiOff size={16} color={palette.white} />
      <Text style={styles.text}>You're offline. Some information may be out of date.</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  banner: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 8,
    paddingVertical: spacing.xs,
    backgroundColor: palette.danger,
  },
  text: { color: palette.white, fontSize: 12, fontWeight: "600" },
});

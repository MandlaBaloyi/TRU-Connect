import React, { useState } from "react";
import { StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { CameraView, useCameraPermissions, type BarcodeScanningResult } from "expo-camera";
import { ScanLine } from "lucide-react-native";

import { Note } from "@/components/lists/CardListUI";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * "Scan Code" tab — genuinely real camera + real QR detection
 * (expo-camera's CameraView, verified against the actual published
 * package before use — its onBarcodeScanned fires with the real
 * decoded string, not a mock). What's honestly NOT real: resolving a
 * scanned code against a real account. There's no backend endpoint to
 * ask "whose code is this" yet, so a successful scan shows the raw
 * decoded value and says so plainly, rather than pretending a
 * connection was made.
 *
 * scannedValue-guard stops onBarcodeScanned firing dozens of times per
 * second while the same code stays in frame — without it, "Scan
 * again" would need to fight a callback still actively re-triggering
 * underneath it.
 */
export function ScanCodeTab() {
  const theme = useTheme();
  const [permission, requestPermission] = useCameraPermissions();
  const [scannedValue, setScannedValue] = useState<string | null>(null);

  const handleScan = (result: BarcodeScanningResult) => {
    if (scannedValue) return; // already showing a result — ignore further scans
    setScannedValue(result.data);
  };

  if (!permission) {
    return <View style={styles.centre} />;
  }

  if (!permission.granted) {
    return (
      <View style={styles.permissionWrap}>
        <ScanLine size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />
        <Text style={[styles.permissionText, { color: theme.colors.onSurfaceVariant }]}>
          TruConnect needs camera access to scan a Connect Code.
        </Text>
        <PrimaryButton onPress={requestPermission}>Allow camera access</PrimaryButton>
      </View>
    );
  }

  if (scannedValue) {
    return (
      <View style={styles.resultWrap}>
        <Text style={[styles.resultTitle, { color: theme.colors.onSurface }]}>Code detected</Text>
        <View style={[styles.resultCard, { backgroundColor: theme.colors.surfaceVariant }]}>
          <Text style={[styles.resultValue, { color: theme.colors.onSurfaceVariant }]} numberOfLines={2}>
            {scannedValue}
          </Text>
        </View>
        <Note>
          Connecting via a scanned code isn't wired up to the backend yet — this is only showing what the camera
          actually read.
        </Note>
        <PrimaryButton onPress={() => setScannedValue(null)}>Scan again</PrimaryButton>
      </View>
    );
  }

  return (
    <View style={styles.cameraWrap}>
      <CameraView
        style={StyleSheet.absoluteFill}
        facing="back"
        barcodeScannerSettings={{ barcodeTypes: ["qr"] }}
        onBarcodeScanned={handleScan}
      />
      <View style={styles.frameOverlay} pointerEvents="none">
        <View style={[styles.frame, { borderColor: theme.colors.background }]} />
      </View>
      <Text style={[styles.hint, { color: theme.colors.background }]}>Point your camera at a Connect Code</Text>
    </View>
  );
}

const styles = StyleSheet.create({
  centre: { flex: 1 },
  permissionWrap: { flex: 1, alignItems: "center", justifyContent: "center", gap: spacing.md, padding: spacing.lg },
  permissionText: { ...typography.body, textAlign: "center" },
  resultWrap: { flex: 1, padding: spacing.md, gap: spacing.md, justifyContent: "center" },
  resultTitle: { ...typography.h2, textAlign: "center" },
  resultCard: { borderRadius: radius.lg, padding: spacing.md },
  resultValue: { ...typography.bodySmall },
  cameraWrap: { flex: 1, backgroundColor: "#000000" },
  frameOverlay: { position: "absolute", top: 0, left: 0, right: 0, bottom: 0, alignItems: "center", justifyContent: "center" },
  frame: { width: 220, height: 220, borderRadius: radius.lg, borderWidth: 2 },
  hint: { ...typography.body, position: "absolute", bottom: spacing.xxl, alignSelf: "center", fontWeight: "600" },
});

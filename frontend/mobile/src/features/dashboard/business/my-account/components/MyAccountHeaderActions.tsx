/**
 * My Account's header-right actions — pencil opens the consolidated
 * Profile editor, QR opens this account's Connect Code. Supplied via
 * the index screen's own options.headerRight (FeatureHeader already
 * reads this per-screen, see that component's own docstring — no
 * changes needed there).
 *
 * Grouped in one row with a small fixed gap so the two icons sit
 * tight together rather than spreading apart — the same layout fix
 * already applied to AppHeader's own secondaryRightIcon/rightIcon
 * pairing (Community's search+overflow icons); FeatureHeader's
 * rightSlot has no such bug since it renders whatever this returns
 * as a single unit, but the same tight-grouping intent applies.
 */
import React from "react";
import { Pressable, StyleSheet, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { QrCode, SquarePen } from "lucide-react-native";

interface Props {
  profileRoute: string;
  qrCodeRoute: string;
}

export function MyAccountHeaderActions({ profileRoute, qrCodeRoute }: Props) {
  const router = useRouter();
  const theme = useTheme();

  return (
    <View style={styles.row}>
      <Pressable
        onPress={() => router.push(profileRoute as any)}
        hitSlop={10}
        style={styles.iconButton}
        accessibilityRole="button"
        accessibilityLabel="Edit profile"
      >
        <SquarePen size={20} color={theme.colors.onSurface} />
      </Pressable>
      <Pressable
        onPress={() => router.push(qrCodeRoute as any)}
        hitSlop={10}
        style={styles.iconButton}
        accessibilityRole="button"
        accessibilityLabel="My QR code"
      >
        <QrCode size={20} color={theme.colors.onSurface} />
      </Pressable>
    </View>
  );
}

const styles = StyleSheet.create({
  row: { flexDirection: "row", alignItems: "center", gap: 4 },
  iconButton: { padding: 4 },
});

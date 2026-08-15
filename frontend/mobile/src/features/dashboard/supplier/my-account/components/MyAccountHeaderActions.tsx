/**
 * My Account's header-right actions, supplier side. Mirrors
 * business/my-account/components/MyAccountHeaderActions.tsx exactly —
 * see that file's own docstring.
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

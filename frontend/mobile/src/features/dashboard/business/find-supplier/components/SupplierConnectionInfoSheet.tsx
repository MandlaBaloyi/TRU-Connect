import React from "react";
import { Modal, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Handshake } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  visible: boolean;
  supplierName: string;
  onClose: () => void;
}

/**
 * "About connections" -- the explainer that used to sit as a grey
 * paragraph under the Request Connection button. Moved into the
 * profile's ⋮ menu so the screen leads with the supplier's brand and
 * products, not process copy.
 *
 * Same Modal + backdrop + bottom-sheet pattern as ContactSupplierSheet
 * / ImageActionSheet.
 *
 * SCOPED TO "HOW IT WORKS", NOT "WHAT THIS STATUS MEANS". This briefly
 * also listed every status label with its meaning -- removed as a
 * duplicate once each status grew its own ⓘ on the profile card
 * (SupplierConnectionStatus.tsx). Two copies of the same wording in
 * two places is exactly how they drift apart; the explanation now
 * lives next to the thing it explains, and this sheet stays about the
 * three-step process.
 */
const STEPS = [
  {
    title: "1 · You request a connection",
    body: "The supplier is notified that you'd like to order stock from them. Nothing is shared beyond your business name.",
  },
  {
    title: "2 · They approve or decline",
    body: "Until they approve, your request stays pending. You can still browse their full catalogue in the meantime.",
  },
  {
    title: "3 · You're connected",
    body: "Once approved, you can place stock orders and see the supplier's contact details and collection address.",
  },
];

export function SupplierConnectionInfoSheet({ visible, supplierName, onClose }: Props) {
  const theme = useTheme();
  const insets = useSafeAreaInsets();

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose}>
        <Pressable
          style={[
            styles.sheet,
            { backgroundColor: theme.colors.background, paddingBottom: spacing.lg + insets.bottom },
          ]}
          onPress={() => {}}
        >
          <View style={[styles.grabber, { backgroundColor: theme.colors.outlineVariant }]} />

          <View style={styles.header}>
            <View style={[styles.iconWrap, { backgroundColor: theme.colors.primaryContainer }]}>
              <Handshake size={22} color={theme.colors.primary} strokeWidth={2} />
            </View>
            <Text style={[styles.title, { color: theme.colors.onSurface }]}>How connecting works</Text>
            <Text style={[styles.subtitle, { color: theme.colors.onSurfaceVariant }]}>
              A connection is how you and {supplierName} agree to trade on TruConnect.
            </Text>
          </View>

          {STEPS.map((step) => (
            <View key={step.title} style={styles.step}>
              <Text style={[styles.stepTitle, { color: theme.colors.onSurface }]}>{step.title}</Text>
              <Text style={[styles.stepBody, { color: theme.colors.onSurfaceVariant }]}>{step.body}</Text>
            </View>
          ))}

          <Pressable
            onPress={onClose}
            style={[styles.done, { backgroundColor: theme.colors.primary }]}
            accessibilityRole="button"
            accessibilityLabel="Got it"
          >
            <Text style={[styles.doneText, { color: theme.colors.onPrimary }]}>Got it</Text>
          </Pressable>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.45)", justifyContent: "flex-end" },
  sheet: {
    borderTopLeftRadius: radius.lg,
    borderTopRightRadius: radius.lg,
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.sm,
    gap: spacing.md,
  },
  grabber: { alignSelf: "center", width: 36, height: 4, borderRadius: 2, marginBottom: spacing.xs },
  header: { alignItems: "center", gap: spacing.xs },
  iconWrap: { width: 48, height: 48, borderRadius: 24, alignItems: "center", justifyContent: "center" },
  title: { ...typography.h2, fontWeight: "700", textAlign: "center" },
  subtitle: { ...typography.bodySmall, textAlign: "center", lineHeight: 18 },
  step: { gap: 2 },
  stepTitle: { ...typography.body, fontWeight: "700" },
  stepBody: { ...typography.bodySmall, lineHeight: 19 },
  done: { minHeight: 48, borderRadius: radius.md, alignItems: "center", justifyContent: "center", marginTop: spacing.xs },
  doneText: { ...typography.body, fontWeight: "700" },
});

/**
 * ReceiptPreviewModal — shows LoanReceiptCard ON-SCREEN, for "View
 * receipt" (as opposed to useShareReceipt's off-screen render, used
 * only for capture).
 *
 * Reuses the exact same component and data shape as sharing — the
 * business owner previews precisely what would be shared, with no
 * separate rendering path to drift out of sync with the real receipt.
 *
 * Uses React Native's built-in Modal — no new dependency, since this is
 * a straightforward overlay, not a native capture operation.
 */

import React from "react";
import { Modal, Pressable, ScrollView, StyleSheet, View } from "react-native";
import { useTheme } from "react-native-paper";
import { X } from "lucide-react-native";

import type { ReceiptData } from "../services/receiptService";
import { LoanReceiptCard } from "./LoanReceiptCard";
import { spacing } from "@/theme/spacing";

interface Props {
  visible: boolean;
  data: ReceiptData | null;
  onClose: () => void;
}

export function ReceiptPreviewModal({ visible, data, onClose }: Props) {
  const theme = useTheme();
  if (!data) return null;

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <View style={[styles.backdrop, { backgroundColor: "rgba(0,0,0,0.5)" }]}>
        <View style={styles.sheet}>
          <Pressable
            onPress={onClose}
            style={[styles.closeButton, { backgroundColor: theme.colors.surfaceVariant }]}
            accessibilityRole="button"
            accessibilityLabel="Close receipt preview"
            hitSlop={8}
          >
            <X size={20} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
          </Pressable>
          <ScrollView contentContainerStyle={styles.scrollContent} bounces={false}>
            <LoanReceiptCard data={data} />
          </ScrollView>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, justifyContent: "flex-end" },
  sheet: {
    maxHeight: "85%",
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    overflow: "hidden",
  },
  closeButton: {
    position: "absolute",
    top: spacing.sm,
    right: spacing.sm,
    zIndex: 1,
    width: 36,
    height: 36,
    borderRadius: 18,
    alignItems: "center",
    justifyContent: "center",
  },
  scrollContent: { flexGrow: 1, alignItems: "center", paddingVertical: spacing.lg },
});

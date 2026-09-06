import React, { useState } from "react";
import { Modal, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Info } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * A small ⓘ that opens a short explanation on tap.
 *
 * WHY THIS EXISTS — explanation was competing with content. Screens had
 * grown a paragraph of grey helper text under every section heading
 * ("Shown on your profile to any business, connected or not…", "Where
 * businesses collect their orders. Only shown to businesses you're
 * connected with."). Each sentence was individually justified, but
 * together they meant a supplier scrolled through more explanation than
 * actual profile, and a business read more process copy than product.
 *
 * Explanation is now OPT-IN: the label says what the thing is, the ⓘ
 * says what it means, and someone who already knows never pays for it.
 *
 * DELIBERATELY A MODAL, NOT AN INLINE EXPANSION. An inline reveal
 * reflows everything below it, which on a form means the field you were
 * about to tap moves. A centred card leaves the layout still.
 *
 * Not a tooltip either: a floating bubble anchored to a 16px icon is
 * fiddly on touch, clips at screen edges, and can't hold more than a
 * few words.
 */
export function InfoHint({
  title,
  body,
  size = 16,
  accessibilityLabel,
  trigger,
}: {
  title: string;
  /** One or more short paragraphs. An array renders as separate
   *  paragraphs rather than one wall of text — used where a hint has to
   *  cover several states (e.g. what each connection status means). */
  body: string | string[];
  size?: number;
  accessibilityLabel?: string;
  /** Use something OTHER than the ⓘ glyph as the tap target — e.g. the
   *  verified tick itself, so the badge explains itself rather than
   *  growing a second icon beside it. */
  trigger?: React.ReactNode;
}) {
  const theme = useTheme();
  const [open, setOpen] = useState(false);
  const paragraphs = Array.isArray(body) ? body : [body];

  return (
    <>
      <Pressable
        onPress={() => setOpen(true)}
        // Generous hitSlop: the icon is deliberately small so it stays
        // subordinate to the label it sits beside, but the TARGET must
        // still clear the ~44px minimum.
        hitSlop={12}
        accessibilityRole="button"
        accessibilityLabel={accessibilityLabel ?? `What does "${title}" mean?`}
      >
        {trigger ?? <Info size={size} color={theme.colors.onSurfaceVariant} strokeWidth={2} />}
      </Pressable>

      <Modal visible={open} animationType="fade" transparent onRequestClose={() => setOpen(false)}>
        <Pressable style={styles.backdrop} onPress={() => setOpen(false)}>
          {/* Inner Pressable swallows the tap so pressing the card
              itself doesn't close it -- same pattern as
              ImageActionSheet / ContactSupplierSheet. */}
          <Pressable style={[styles.card, { backgroundColor: theme.colors.background }]} onPress={() => {}}>
            <Text style={[styles.title, { color: theme.colors.onSurface }]}>{title}</Text>
            {paragraphs.map((paragraph) => (
              <Text key={paragraph} style={[styles.body, { color: theme.colors.onSurfaceVariant }]}>
                {paragraph}
              </Text>
            ))}
            <Pressable
              onPress={() => setOpen(false)}
              style={[styles.done, { backgroundColor: theme.colors.primary }]}
              accessibilityRole="button"
              accessibilityLabel="Got it"
            >
              <Text style={[styles.doneText, { color: theme.colors.onPrimary }]}>Got it</Text>
            </Pressable>
          </Pressable>
        </Pressable>
      </Modal>
    </>
  );
}

const styles = StyleSheet.create({
  backdrop: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.45)",
    alignItems: "center",
    justifyContent: "center",
    padding: spacing.lg,
  },
  card: { width: "100%", maxWidth: 420, borderRadius: radius.lg, padding: spacing.lg, gap: spacing.sm },
  title: { ...typography.h2, fontWeight: "700" },
  body: { ...typography.bodySmall, lineHeight: 20 },
  done: {
    minHeight: 44,
    borderRadius: radius.md,
    alignItems: "center",
    justifyContent: "center",
    marginTop: spacing.xs,
  },
  doneText: { ...typography.body, fontWeight: "700" },
});

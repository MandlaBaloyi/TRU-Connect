import React from "react";
import { Modal, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Mail, MessageCircle, Music2 } from "lucide-react-native";

import { buildTikTokUrl, buildWhatsAppUrl, openUrl } from "@/services/contact/contactLinks";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { SupplierContactDetails } from "../../find-supplier/types";

interface Props {
  visible: boolean;
  supplierName: string;
  /** null renders a real "not available" message, not an empty sheet
   *  -- a business tapping "Contact Supplier" from the menu and
   *  getting nothing at all with no explanation would read as broken,
   *  not as "not connected yet" or "supplier hasn't opted in". */
  contact: SupplierContactDetails | null;
  onClose: () => void;
}

/** Same WhatsApp/TikTok/Email buttons already proven working on
 *  SupplierProductDetailScreen.tsx -- extracted here so the SAME real,
 *  working UI serves both the product detail screen and the
 *  catalogue-level "Contact Supplier" menu item, rather than two
 *  copies that could quietly drift apart. */
export function ContactSupplierSheet({ visible, supplierName, contact, onClose }: Props) {
  const theme = useTheme();

  return (
    <Modal visible={visible} animationType="fade" transparent onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose}>
        <Pressable style={[styles.sheet, { backgroundColor: theme.colors.background }]} onPress={() => {}}>
          <Text style={[styles.title, { color: theme.colors.onSurface }]}>Contact {supplierName}</Text>

          {contact ? (
            <View style={styles.actions}>
              {contact.whatsappNumber && (
                <Pressable
                  onPress={() => openUrl(buildWhatsAppUrl(contact.whatsappNumber!))}
                  style={({ pressed }) => [
                    styles.action,
                    { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface },
                    pressed && styles.actionPressed,
                  ]}
                  accessibilityRole="button"
                  accessibilityLabel={`Message ${supplierName} on WhatsApp`}
                >
                  <MessageCircle size={18} color={theme.colors.onSurface} strokeWidth={2} />
                  <Text style={[styles.actionLabel, { color: theme.colors.onSurface }]}>WhatsApp</Text>
                </Pressable>
              )}
              {contact.tiktokHandle && (
                <Pressable
                  onPress={() => openUrl(buildTikTokUrl(contact.tiktokHandle!))}
                  style={({ pressed }) => [
                    styles.action,
                    { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface },
                    pressed && styles.actionPressed,
                  ]}
                  accessibilityRole="button"
                  accessibilityLabel={`View ${supplierName} on TikTok`}
                >
                  <Music2 size={18} color={theme.colors.onSurface} strokeWidth={2} />
                  <Text style={[styles.actionLabel, { color: theme.colors.onSurface }]}>TikTok</Text>
                </Pressable>
              )}
              {contact.email && (
                <Pressable
                  onPress={() => openUrl(`mailto:${contact.email}`)}
                  style={({ pressed }) => [
                    styles.action,
                    { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface },
                    pressed && styles.actionPressed,
                  ]}
                  accessibilityRole="button"
                  accessibilityLabel={`Email ${supplierName}`}
                >
                  <Mail size={18} color={theme.colors.onSurface} strokeWidth={2} />
                  <Text style={[styles.actionLabel, { color: theme.colors.onSurface }]}>Email</Text>
                </Pressable>
              )}
            </View>
          ) : (
            <Text style={[styles.unavailable, { color: theme.colors.onSurfaceVariant }]}>
              {supplierName} hasn't shared contact details with you yet. This usually means you're not currently
              connected, or they haven't turned this on.
            </Text>
          )}
        </Pressable>
      </Pressable>
    </Modal>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.4)", justifyContent: "flex-end" },
  sheet: { borderTopLeftRadius: radius.lg, borderTopRightRadius: radius.lg, padding: spacing.lg, gap: spacing.md },
  title: { ...typography.h2, fontWeight: "700" },
  actions: { flexDirection: "row", gap: spacing.sm },
  action: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.xs,
    minHeight: 48,
    borderWidth: 1,
    borderRadius: radius.md,
    paddingHorizontal: spacing.sm,
  },
  actionPressed: { opacity: 0.7 },
  actionLabel: { ...typography.body, fontWeight: "600" },
  unavailable: { ...typography.body, lineHeight: 22, paddingBottom: spacing.sm },
});

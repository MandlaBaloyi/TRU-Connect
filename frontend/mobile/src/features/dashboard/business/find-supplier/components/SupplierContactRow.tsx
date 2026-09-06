import React from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Mail, MessageCircle, Music2 } from "lucide-react-native";

import { buildEmailUrl, buildTikTokUrl, buildWhatsAppUrl, openUrl } from "@/services/contact/contactLinks";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { SupplierContactDetails } from "../types";

/**
 * WhatsApp / TikTok / Email as INLINE buttons on the brand profile,
 * rather than the modal ContactSupplierSheet the catalogue's ⋮ menu
 * uses.
 *
 * WHY INLINE AND NOT THE SHEET: WhatsApp is the real channel in this
 * market — an informal business that wants to ask "do you have stock
 * of X" reaches for it immediately, and burying it two taps deep
 * behind a ⋮ menu on a different screen made it effectively invisible.
 * On a profile, contact is a primary action, not an overflow item.
 *
 * (This deliberately does not import my-suppliers' ContactSupplierSheet
 * — my-suppliers depends on THIS feature, not the other way round; the
 * shared URL builders both use now live in services/contact/.)
 *
 * RENDERS NOTHING AT ALL when there's no contact to show. `contact` is
 * null unless the connection is ACTIVE *and* the supplier opted into
 * share_contact_details (see discovery_service.get_supplier_profile's
 * own double gate), and any individual channel can be null within it.
 * An empty row of dead buttons would read as broken; absence is the
 * honest state.
 */
export function SupplierContactRow({ contact }: { contact: SupplierContactDetails | null }) {
  const theme = useTheme();

  if (!contact) return null;
  const { whatsappNumber, tiktokHandle, email } = contact;
  if (!whatsappNumber && !tiktokHandle && !email) return null;

  return (
    <View style={styles.wrap}>
      {whatsappNumber && (
        <ContactButton
          icon={<MessageCircle size={18} color={theme.colors.onSurface} strokeWidth={2} />}
          label="WhatsApp"
          onPress={() => openUrl(buildWhatsAppUrl(whatsappNumber))}
        />
      )}
      {email && (
        <ContactButton
          icon={<Mail size={18} color={theme.colors.onSurface} strokeWidth={2} />}
          label="Email"
          onPress={() => openUrl(buildEmailUrl(email))}
        />
      )}
      {tiktokHandle && (
        <ContactButton
          icon={<Music2 size={18} color={theme.colors.onSurface} strokeWidth={2} />}
          label="TikTok"
          onPress={() => openUrl(buildTikTokUrl(tiktokHandle))}
        />
      )}
    </View>
  );
}

function ContactButton({
  icon,
  label,
  onPress,
}: {
  icon: React.ReactNode;
  label: string;
  onPress: () => void;
}) {
  const theme = useTheme();
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [
        styles.button,
        {
          borderColor: theme.colors.outline,
          backgroundColor: theme.colors.surface,
          opacity: pressed ? 0.7 : 1,
        },
      ]}
      accessibilityRole="button"
      accessibilityLabel={label}
    >
      {icon}
      <Text style={[styles.label, { color: theme.colors.onSurface }]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  wrap: { flexDirection: "row", gap: spacing.sm, paddingHorizontal: spacing.md },
  button: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.xs,
    paddingVertical: spacing.sm,
    borderRadius: radius.lg,
    borderWidth: 1,
  },
  label: { ...typography.bodySmall, fontWeight: "700" },
});

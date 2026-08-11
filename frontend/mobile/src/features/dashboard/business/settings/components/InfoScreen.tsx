import React from "react";
import { Linking, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { ChevronRight, FileText } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";

export interface InfoParagraph {
  heading?: string;
  body: string;
  /** Optional icon shown next to the heading, in a small tinted
   *  circle — purely visual, a paragraph works fine without one. */
  icon?: (color: string) => React.ReactNode;
}

export interface ContactMethod {
  label: string;
  value: string;
  /** tel:, mailto:, or a wa.me link — opened via Linking on tap. */
  url: string;
  icon: (color: string) => React.ReactNode;
}

interface Props {
  paragraphs: InfoParagraph[];
  /** Optional status line shown at the top, e.g. Offline mode's
   *  "Offline-ready" — for INFORMATIONAL screens that describe a
   *  capability the app genuinely already has. */
  statusLabel?: string;
  /** Optional "Last updated ..." / version line for legal documents —
   *  shown right below the status area, above the first paragraph. */
  metaLine?: string;
  /** Optional tappable contact methods (Help & support). Rendered as
   *  their own distinct block, each opening the real phone/email/
   *  WhatsApp app via Linking. */
  contacts?: ContactMethod[];
}

/**
 * Redesigned long-form content screen — used by every INFORMATIONAL
 * and REAL-static entry (Offline mode, Data usage, Help & support,
 * Privacy policy, Terms of service, About). Each paragraph now renders
 * as its own card (icon, heading, body) instead of plain stacked text,
 * per direct feedback asking for something visually distinct from the
 * rest of Settings.
 */
export function InfoScreen({ paragraphs, statusLabel, metaLine, contacts }: Props) {
  const theme = useTheme();

  const openContact = (url: string) => {
    Linking.openURL(url).catch(() => {
      // Silently ignored -- if the device has no app that can handle
      // this URL scheme (e.g. no phone app on a tablet), there's
      // nothing useful to show the user beyond the tap simply not
      // doing anything.
    });
  };

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        {(statusLabel || metaLine) && (
          <View style={styles.metaRow}>
            {statusLabel && (
              <View style={[styles.statusPill, { backgroundColor: theme.colors.secondaryContainer }]}>
                <Text style={[styles.statusText, { color: theme.colors.secondary }]}>{statusLabel}</Text>
              </View>
            )}
            {metaLine && <Text style={[styles.metaLine, { color: theme.colors.onSurfaceVariant }]}>{metaLine}</Text>}
          </View>
        )}

        {contacts && contacts.length > 0 && (
          <View style={[styles.contactCard, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}>
            {contacts.map((contact, index) => (
              <React.Fragment key={contact.label}>
                <Pressable onPress={() => openContact(contact.url)} style={styles.contactRow} accessibilityRole="button" accessibilityLabel={contact.label}>
                  <View style={[styles.contactIconWrap, { backgroundColor: theme.colors.primaryContainer }]}>
                    {contact.icon(theme.colors.primary)}
                  </View>
                  <View style={styles.contactTextWrap}>
                    <Text style={[styles.contactLabel, { color: theme.colors.onSurfaceVariant }]}>{contact.label}</Text>
                    <Text style={[styles.contactValue, { color: theme.colors.onSurface }]}>{contact.value}</Text>
                  </View>
                  <ChevronRight size={18} color={theme.colors.onSurfaceVariant} />
                </Pressable>
                {index < contacts.length - 1 && (
                  <View style={[styles.contactDivider, { backgroundColor: theme.colors.outlineVariant }]} />
                )}
              </React.Fragment>
            ))}
          </View>
        )}

        {paragraphs.map((paragraph, index) => (
          <View key={index} style={[styles.card, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}>
            {paragraph.heading && (
              <View style={styles.cardHeadingRow}>
                <View style={[styles.cardIconWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
                  {paragraph.icon ? paragraph.icon(theme.colors.onSurfaceVariant) : <FileText size={16} color={theme.colors.onSurfaceVariant} />}
                </View>
                <Text style={[styles.heading, { color: theme.colors.onSurface }]}>{paragraph.heading}</Text>
              </View>
            )}
            <Text style={[styles.body, { color: theme.colors.onSurfaceVariant }]}>{paragraph.body}</Text>
          </View>
        ))}
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, gap: spacing.md },
  metaRow: { gap: spacing.xs },
  statusPill: { alignSelf: "flex-start", paddingHorizontal: spacing.md, paddingVertical: spacing.xs, borderRadius: radius.pill },
  statusText: { ...typography.bodySmall, fontWeight: "700" },
  metaLine: { ...typography.bodySmall },
  contactCard: { borderRadius: radius.lg, borderWidth: 1, overflow: "hidden" },
  contactRow: { flexDirection: "row", alignItems: "center", gap: spacing.md, padding: spacing.md, minHeight: 64 },
  contactIconWrap: { width: 40, height: 40, borderRadius: 20, alignItems: "center", justifyContent: "center" },
  contactTextWrap: { flex: 1, gap: 2 },
  contactLabel: { ...typography.bodySmall },
  contactValue: { ...typography.body, fontWeight: "700" },
  contactDivider: { height: StyleSheet.hairlineWidth, marginLeft: spacing.md + 40 + spacing.md },
  card: { borderRadius: radius.lg, borderWidth: 1, padding: spacing.md, gap: spacing.xs },
  cardHeadingRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  cardIconWrap: { width: 28, height: 28, borderRadius: 14, alignItems: "center", justifyContent: "center" },
  heading: { ...typography.h2, flexShrink: 1 },
  body: { ...typography.body, lineHeight: 22 },
});

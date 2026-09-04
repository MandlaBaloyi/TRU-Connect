import React, { useState } from "react";
import { Alert, Linking, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { ChevronDown, ChevronRight, FileText } from "lucide-react-native";

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

export interface DownloadLink {
  label: string;
  /** Omit while no real, hosted URL exists yet -- the button still
   *  renders (so the affordance is genuinely visible now), but taps
   *  show an honest "Coming soon" message instead of silently
   *  failing on a fake or missing URL. Fill this in once the signed
   *  PDF / permanent web page from the policy documents' own
   *  "working draft" notice actually exists somewhere real. */
  url?: string;
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
  /** Renders each card as a real expand/collapse accordion (down
   *  arrow closed, up arrow open) instead of always-expanded text —
   *  opt-in, defaulting to false, so every existing short-content
   *  screen (Offline Mode, About, Data Usage, Help & Support) keeps
   *  its current behavior unchanged. Built specifically for the real,
   *  genuinely long Terms of Service and Privacy Policy documents,
   *  where scrolling past everything always-expanded to find one
   *  section is a real, worse experience than a short screen's own
   *  handful of paragraphs. */
  collapsible?: boolean;
  /** Optional "Download as Word" action, shown as its own card above
   *  the paragraphs. Genuinely tappable once a real, hosted URL
   *  exists for this document -- see this prop's own call site for
   *  the honest current placeholder state. */
  downloadLink?: DownloadLink;
}

/**
 * Redesigned long-form content screen — used by every INFORMATIONAL
 * and REAL-static entry (Offline mode, Data usage, Help & support,
 * Privacy policy, Terms of service, About). Each paragraph now renders
 * as its own card (icon, heading, body) instead of plain stacked text,
 * per direct feedback asking for something visually distinct from the
 * rest of Settings.
 */
export function InfoScreen({ paragraphs, statusLabel, metaLine, contacts, collapsible = false, downloadLink }: Props) {
  const theme = useTheme();
  // Only the FIRST section starts open on a collapsible screen -- a
  // genuinely long legal document collapsed by default reads as "here
  // is the real structure, open what you need," not an overwhelming
  // wall of always-expanded legal text.
  const [openIndex, setOpenIndex] = useState<number | null>(0);

  const openContact = (url: string) => {
    Linking.openURL(url).catch(() => {
      // Silently ignored -- if the device has no app that can handle
      // this URL scheme (e.g. no phone app on a tablet), there's
      // nothing useful to show the user beyond the tap simply not
      // doing anything.
    });
  };

  const openDownload = (link: DownloadLink) => {
    if (!link.url) {
      Alert.alert("Coming soon", "A downloadable version of this document isn't available yet.");
      return;
    }
    Linking.openURL(link.url).catch(() => {
      // Silently ignored, same reasoning as openContact above.
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

        {downloadLink && (
          <Pressable
            onPress={() => openDownload(downloadLink)}
            style={[styles.downloadCard, { backgroundColor: theme.colors.primaryContainer }]}
            accessibilityRole="button"
            accessibilityLabel={downloadLink.label}
          >
            <FileText size={18} color={theme.colors.primary} strokeWidth={2.2} />
            <Text style={[styles.downloadLabel, { color: theme.colors.primary }]}>{downloadLink.label}</Text>
          </Pressable>
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

        {paragraphs.map((paragraph, index) => {
          const isOpen = !collapsible || openIndex === index;
          return (
            <View key={index} style={[styles.card, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}>
              <Pressable
                onPress={collapsible ? () => setOpenIndex(isOpen ? null : index) : undefined}
                style={styles.cardHeadingRow}
                accessibilityRole={collapsible ? "button" : undefined}
                accessibilityState={collapsible ? { expanded: isOpen } : undefined}
              >
                {paragraph.heading && (
                  <>
                    <View style={[styles.cardIconWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
                      {paragraph.icon ? paragraph.icon(theme.colors.onSurfaceVariant) : <FileText size={16} color={theme.colors.onSurfaceVariant} />}
                    </View>
                    <Text style={[styles.heading, { color: theme.colors.onSurface }]}>{paragraph.heading}</Text>
                  </>
                )}
                {collapsible && (
                  <View style={styles.chevronWrap}>
                    {isOpen ? (
                      <ChevronDown size={20} color={theme.colors.onSurfaceVariant} strokeWidth={2.4} />
                    ) : (
                      <ChevronRight size={20} color={theme.colors.onSurfaceVariant} strokeWidth={2.4} />
                    )}
                  </View>
                )}
              </Pressable>
              {isOpen && <Text style={[styles.body, { color: theme.colors.onSurfaceVariant }]}>{paragraph.body}</Text>}
            </View>
          );
        })}
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
  downloadCard: { flexDirection: "row", alignItems: "center", gap: spacing.sm, borderRadius: radius.lg, padding: spacing.md, minHeight: 52 },
  downloadLabel: { ...typography.body, fontWeight: "700" },
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
  chevronWrap: { marginLeft: "auto" },
  heading: { ...typography.h2, flexShrink: 1 },
  body: { ...typography.body, lineHeight: 22, marginTop: spacing.xs },
});

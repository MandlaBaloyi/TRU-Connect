import React from "react";
import { Pressable, StyleSheet, Switch, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { ChevronRight } from "lucide-react-native";

import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * Shared card-based list system — rounded cards with real padding,
 * icon circles, and a hero section pattern. Originally built for
 * Account Security, then promoted here so Settings and More share the
 * exact same visual language rather than three features each
 * reinventing "a list of rows that opens something" slightly
 * differently. Security's own components/SecurityUI.tsx now re-exports
 * from here under its original names, so nothing there needed to
 * change.
 */

/** Icon + short explanation at the top of a screen. */
export function Hero({ icon, title, description }: { icon: React.ReactNode; title: string; description: string }) {
  const theme = useTheme();
  return (
    <View style={styles.hero}>
      <View style={[styles.heroIcon, { backgroundColor: theme.colors.primaryContainer }]}>{icon}</View>
      <Text style={[styles.heroTitle, { color: theme.colors.onSurface }]}>{title}</Text>
      <Text style={[styles.heroBody, { color: theme.colors.onSurfaceVariant }]}>{description}</Text>
    </View>
  );
}

/** ON/OFF style status — colour AND text together, never colour alone. */
export function StatusPill({ label, tone }: { label: string; tone: "on" | "off" | "warning" }) {
  const theme = useTheme();
  const palette = {
    on: { bg: theme.colors.secondaryContainer, fg: theme.colors.secondary },
    off: { bg: theme.colors.surfaceVariant, fg: theme.colors.onSurfaceVariant },
    warning: { bg: theme.colors.errorContainer, fg: theme.colors.error },
  }[tone];
  return (
    <View style={[stylesInline.pill, { backgroundColor: palette.bg }]}>
      <Text style={[stylesInline.pillText, { color: palette.fg }]}>{label}</Text>
    </View>
  );
}

export function CardSection({ title, children }: { title?: string; children: React.ReactNode }) {
  const theme = useTheme();
  return (
    <View style={styles.section}>
      {title && <Text style={[styles.sectionTitle, { color: theme.colors.onSurfaceVariant }]}>{title}</Text>}
      <View style={styles.cardStack}>{children}</View>
    </View>
  );
}

/** A single tappable card. */
export function Card({
  icon,
  label,
  description,
  status,
  onPress,
  disabled,
}: {
  icon?: (color: string) => React.ReactNode;
  label: string;
  description?: string;
  status?: React.ReactNode;
  onPress: () => void;
  disabled?: boolean;
}) {
  const theme = useTheme();
  return (
    <Pressable
      onPress={onPress}
      disabled={disabled}
      style={({ pressed }) => [
        styles.card,
        {
          backgroundColor: theme.colors.surface,
          borderColor: theme.colors.outlineVariant,
          opacity: disabled ? 0.5 : pressed ? 0.85 : 1,
        },
      ]}
      accessibilityRole="button"
      accessibilityLabel={label}
    >
      {icon && (
        <View style={[styles.iconWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
          {icon(theme.colors.onSurfaceVariant)}
        </View>
      )}
      <View style={styles.cardText}>
        <Text style={[styles.cardLabel, { color: theme.colors.onSurface }]}>{label}</Text>
        {description && (
          <Text style={[styles.cardDescription, { color: theme.colors.onSurfaceVariant }]}>{description}</Text>
        )}
      </View>
      {status}
      <ChevronRight size={18} color={theme.colors.onSurfaceVariant} />
    </Pressable>
  );
}

/** Same visual language as Card, but with a real Switch instead of a
 *  chevron — for genuinely functional toggles only (see this app's
 *  own rule against fake switches: a control must never appear
 *  functional when it isn't). */
export function SwitchCard({
  icon,
  label,
  description,
  value,
  onValueChange,
}: {
  icon?: (color: string) => React.ReactNode;
  label: string;
  description?: string;
  value: boolean;
  onValueChange: (value: boolean) => void;
}) {
  const theme = useTheme();
  return (
    <View style={[styles.card, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}>
      {icon && (
        <View style={[styles.iconWrap, { backgroundColor: theme.colors.surfaceVariant }]}>
          {icon(theme.colors.onSurfaceVariant)}
        </View>
      )}
      <View style={styles.cardText}>
        <Text style={[styles.cardLabel, { color: theme.colors.onSurface }]}>{label}</Text>
        {description && (
          <Text style={[styles.cardDescription, { color: theme.colors.onSurfaceVariant }]}>{description}</Text>
        )}
      </View>
      <Switch value={value} onValueChange={onValueChange} accessibilityLabel={label} />
    </View>
  );
}

/** A non-navigating card for entries that just display information. */
export function ListCard({
  title,
  subtitle,
  meta,
  badge,
  action,
}: {
  title: string;
  subtitle?: string | null;
  meta?: string;
  badge?: React.ReactNode;
  action?: React.ReactNode;
}) {
  const theme = useTheme();
  return (
    <View style={[styles.card, { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant }]}>
      <View style={styles.cardText}>
        <View style={styles.itemTitleRow}>
          <Text style={[styles.cardLabel, { color: theme.colors.onSurface }]}>{title}</Text>
          {badge}
        </View>
        {subtitle && (
          <Text style={[styles.cardDescription, { color: theme.colors.onSurfaceVariant }]}>{subtitle}</Text>
        )}
        {meta && <Text style={[styles.itemMeta, { color: theme.colors.onSurfaceVariant }]}>{meta}</Text>}
      </View>
      {action}
    </View>
  );
}

/** A plain informational note beneath the main content. */
export function Note({ children }: { children: React.ReactNode }) {
  const theme = useTheme();
  return (
    <View style={[styles.note, { backgroundColor: theme.colors.surfaceVariant }]}>
      <Text style={[styles.noteText, { color: theme.colors.onSurfaceVariant }]}>{children}</Text>
    </View>
  );
}

/** Friendly relative time — no raw timestamps in the UI. */
export function formatWhen(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diffMs / 60_000);
  if (mins < 1) return "Just now";
  if (mins < 60) return `${mins} minute${mins === 1 ? "" : "s"} ago`;
  const hours = Math.floor(mins / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  const days = Math.floor(hours / 24);
  if (days < 30) return `${days} day${days === 1 ? "" : "s"} ago`;
  const months = Math.floor(days / 30);
  if (months < 12) return `${months} month${months === 1 ? "" : "s"} ago`;
  const years = Math.floor(months / 12);
  return `${years} year${years === 1 ? "" : "s"} ago`;
}

const styles = StyleSheet.create({
  hero: { alignItems: "center", gap: spacing.sm, paddingVertical: spacing.md, paddingHorizontal: spacing.md },
  heroIcon: { width: 64, height: 64, borderRadius: 32, alignItems: "center", justifyContent: "center" },
  heroTitle: { ...typography.h1, textAlign: "center" },
  heroBody: { ...typography.body, textAlign: "center", lineHeight: 22 },
  section: { gap: spacing.sm },
  sectionTitle: { ...typography.bodySmall, fontWeight: "700", textTransform: "uppercase", letterSpacing: 0.5 },
  cardStack: { gap: spacing.sm },
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    padding: spacing.md,
    borderRadius: radius.lg,
    borderWidth: 1,
  },
  itemTitleRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm },
  iconWrap: { width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center" },
  cardText: { flex: 1, gap: 2 },
  cardLabel: { ...typography.body, fontWeight: "700" },
  cardDescription: { ...typography.bodySmall },
  itemMeta: { ...typography.bodySmall, opacity: 0.8 },
  note: { padding: spacing.md, borderRadius: radius.lg, marginTop: spacing.xs },
  noteText: { ...typography.bodySmall, lineHeight: 19 },
});

const stylesInline = StyleSheet.create({
  pill: { paddingHorizontal: spacing.sm, paddingVertical: 3, borderRadius: radius.pill },
  pillText: { ...typography.bodySmall, fontWeight: "700" },
});

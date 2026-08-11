import React from "react";
import { Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Check } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { Hero } from "@/components/lists/CardListUI";
import { spacing, radius } from "@/theme/spacing";
import { typography } from "@/theme/typography";

export interface PickerOption<T extends string> {
  value: T;
  label: string;
  description?: string;
  /** Optional icon, rendered in a soft tinted circle on the left —
   *  Theme uses sun/moon/phone, Default start screen uses a per-tab
   *  icon. A function of the icon's own colour (not a fixed element)
   *  because that colour must adapt to whether this option is
   *  currently selected — a white icon on a light unselected
   *  background would be invisible. Purely visual; a picker works
   *  fine without one. */
  icon?: (color: string) => React.ReactNode;
}

interface Props<T extends string> {
  /** Icon + title + description shown above the options — the same
   *  pattern as Account Security's internal screens (Password, 2FA,
   *  etc.): icon, then words, then the choices themselves. Optional so
   *  a picker still works without one, but every current caller
   *  (Theme, Language, Default start screen) supplies one. */
  hero?: { icon: React.ReactNode; title: string; description: string };
  options: PickerOption<T>[];
  selected: T;
  onSelect: (value: T) => void;
  /** Optional note under the list — used by Language to honestly list
   *  what's planned but not yet available. */
  footnote?: string;
  /** Optional not-yet-available options, shown in their own clearly
   *  separate section. Used ONLY where offering them as selectable
   *  would be a lie (e.g. languages with no translations yet). */
  unavailableOptions?: string[];
  unavailableSectionLabel?: string;
}

/**
 * Redesigned single-select picker — individual rounded cards instead
 * of a flat divided list, per direct feedback asking for something
 * visually distinct from the rest of Settings. Selection applies
 * immediately (no separate Save button, matching standard mobile
 * settings behaviour); the selected card gets a tinted background,
 * coloured border, and filled check circle so the current choice is
 * unambiguous at a glance.
 */
export function OptionPickerScreen<T extends string>({
  hero,
  options,
  selected,
  onSelect,
  footnote,
  unavailableOptions,
  unavailableSectionLabel = "Coming soon",
}: Props<T>) {
  const theme = useTheme();

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        {hero && <Hero icon={hero.icon} title={hero.title} description={hero.description} />}

        <View style={styles.cardStack}>
          {options.map((option) => {
            const isSelected = option.value === selected;
            return (
              <Pressable
                key={option.value}
                onPress={() => onSelect(option.value)}
                style={[
                  styles.card,
                  {
                    backgroundColor: isSelected ? theme.colors.primaryContainer : theme.colors.surface,
                    borderColor: isSelected ? theme.colors.primary : theme.colors.outlineVariant,
                  },
                ]}
                accessibilityRole="radio"
                accessibilityState={{ selected: isSelected }}
                accessibilityLabel={option.label}
              >
                {option.icon && (
                  <View
                    style={[
                      styles.iconWrap,
                      { backgroundColor: isSelected ? theme.colors.primary : theme.colors.surfaceVariant },
                    ]}
                  >
                    {option.icon(isSelected ? theme.colors.onPrimary : theme.colors.onSurfaceVariant)}
                  </View>
                )}
                <View style={styles.textWrap}>
                  <Text style={[styles.label, { color: theme.colors.onSurface }]}>{option.label}</Text>
                  {option.description && (
                    <Text style={[styles.description, { color: theme.colors.onSurfaceVariant }]}>
                      {option.description}
                    </Text>
                  )}
                </View>
                <View
                  style={[
                    styles.radio,
                    {
                      borderColor: isSelected ? theme.colors.primary : theme.colors.outline,
                      backgroundColor: isSelected ? theme.colors.primary : "transparent",
                    },
                  ]}
                >
                  {isSelected && <Check size={14} color={theme.colors.onPrimary} strokeWidth={3} />}
                </View>
              </Pressable>
            );
          })}
        </View>

        {unavailableOptions && unavailableOptions.length > 0 && (
          <View style={styles.unavailableSection}>
            <Text style={[styles.unavailableSectionLabel, { color: theme.colors.onSurfaceVariant }]}>
              {unavailableSectionLabel}
            </Text>
            <View style={styles.unavailableWrap}>
              {unavailableOptions.map((label) => (
                <View key={label} style={[styles.unavailableChip, { backgroundColor: theme.colors.surfaceVariant }]}>
                  <Text style={[styles.unavailableChipText, { color: theme.colors.onSurfaceVariant }]}>{label}</Text>
                </View>
              ))}
            </View>
          </View>
        )}

        {footnote && <Text style={[styles.footnote, { color: theme.colors.onSurfaceVariant }]}>{footnote}</Text>}
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.lg },
  cardStack: { gap: spacing.sm },
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    padding: spacing.md,
    borderRadius: radius.lg,
    borderWidth: 1.5,
  },
  iconWrap: { width: 44, height: 44, borderRadius: 22, alignItems: "center", justifyContent: "center" },
  textWrap: { flex: 1, gap: 2 },
  label: { ...typography.body, fontWeight: "700" },
  description: { ...typography.bodySmall },
  radio: { width: 24, height: 24, borderRadius: 12, borderWidth: 2, alignItems: "center", justifyContent: "center" },
  unavailableSection: { gap: spacing.sm },
  unavailableSectionLabel: { ...typography.bodySmall, fontWeight: "700", textTransform: "uppercase", letterSpacing: 0.5 },
  unavailableWrap: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  unavailableChip: { paddingHorizontal: spacing.md, paddingVertical: spacing.sm, borderRadius: radius.pill, opacity: 0.6 },
  unavailableChipText: { ...typography.bodySmall, fontWeight: "600" },
  footnote: { ...typography.bodySmall, lineHeight: 20 },
});

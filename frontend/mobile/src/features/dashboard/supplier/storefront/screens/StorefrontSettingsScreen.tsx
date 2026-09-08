import React, { useEffect, useState } from "react";
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { Switch, useTheme } from "react-native-paper";
import { ChevronDown, ChevronUp, Plus, Star, Trash2 } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ErrorState } from "@/components/feedback/ErrorState";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { ApiError } from "@/services/api/apiClient";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { SectionEditorSheet } from "../components/SectionEditorSheet";
import { useStorefrontConfig } from "../useStorefrontConfig";
import {
  MAX_CURATED_SECTIONS,
  SECTION_COPY,
  type StorefrontConfigSection,
} from "../types";

/**
 * The supplier's control over their own shopfront: which of the six
 * sections a business sees, in what order, and what goes in the two
 * they choose themselves.
 *
 * EDITS ARE LOCAL UNTIL SAVED, deliberately. Reordering is a sequence
 * of small moves -- up, up, down -- and saving each one would fire a
 * request per tap and leave the storefront briefly in orders the
 * supplier was only passing through. They arrange it, then commit it.
 *
 * EVERY SECTION SAYS WHAT MAKES IT APPEAR. "Why is my sale section not
 * showing" is the question this screen exists to answer before it gets
 * asked, so each row carries the rule in plain terms rather than only
 * a name and a switch (see SECTION_COPY).
 *
 * A SWITCHED-ON SECTION CAN STILL BE EMPTY, and the screen says so
 * rather than pretending otherwise. Best sellers stays hidden until
 * businesses have actually bought; bulk needs pack sizes on products.
 * That is the honest behaviour, and a supplier who does not know it is
 * a support conversation waiting to happen.
 */
export default function StorefrontSettingsScreen() {
  const theme = useTheme();
  const { sections, isLoading, isError, refetch, save, isSaving } = useStorefrontConfig();

  const [draft, setDraft] = useState<StorefrontConfigSection[]>([]);
  const [isDirty, setIsDirty] = useState(false);
  // The section currently open in the editor, by index. A modal rather
  // than a route because the draft above is unsaved -- see
  // SectionEditorSheet's own docstring.
  const [editingIndex, setEditingIndex] = useState<number | null>(null);

  // Seed the draft once the real configuration arrives, and re-seed
  // after a save. Guarded on isDirty so a background refetch can never
  // wipe edits the supplier has made but not yet saved.
  useEffect(() => {
    if (!isDirty && sections.length > 0) setDraft(sections);
  }, [sections, isDirty]);

  const update = (next: StorefrontConfigSection[]) => {
    setDraft(next);
    setIsDirty(true);
  };

  const move = (index: number, direction: -1 | 1) => {
    const target = index + direction;
    if (target < 0 || target >= draft.length) return;
    const next = [...draft];
    [next[index], next[target]] = [next[target], next[index]];
    update(next);
  };

  const toggle = (index: number, isEnabled: boolean) => {
    const next = [...draft];
    next[index] = { ...next[index], isEnabled };
    update(next);
  };

  const removeCurated = (index: number) => {
    Alert.alert("Remove this shelf?", "The products stay in your catalogue — only the shelf goes.", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Remove",
        style: "destructive",
        onPress: () => update(draft.filter((_, position) => position !== index)),
      },
    ]);
  };

  const handleSave = async () => {
    try {
      await save(draft);
      setIsDirty(false);
    } catch (error) {
      // The backend's own validation messages are already written for
      // a supplier ("Pick at least 3 products for your strip"), so
      // they are shown as-is rather than reworded into something
      // vaguer.
      Alert.alert(
        "Couldn't save your storefront",
        error instanceof ApiError ? error.message : "Check your connection and try again."
      );
    }
  };

  if (isLoading) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  if (isError) {
    return (
      <ScreenContainer hasNativeHeader>
        <ErrorState
          message="Couldn't load your storefront settings. Check your connection and try again."
          onRetry={refetch}
        />
      </ScreenContainer>
    );
  }

  const curatedCount = draft.filter((section) => section.type === "CURATED").length;
  const hasFeatured = draft.some((section) => section.type === "FEATURED_PRODUCT");

  return (
    <ScreenContainer hasNativeHeader paddingHorizontal={0}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.body}>
          <SectionHeading
            title="Your storefront"
            hint={[
              "These sections sit at the top of your profile, above your categories, and are the first thing a business sees.",
              "The order here is the order they appear in. Move the ones that sell to the top.",
              "A section that is switched on can still be empty — each one below says what makes it appear.",
            ]}
          />

          {draft.map((section, index) => (
            <SectionRow
              key={section.id ?? `${section.type}-${index}`}
              section={section}
              isFirst={index === 0}
              isLast={index === draft.length - 1}
              onToggle={(value) => toggle(index, value)}
              onMoveUp={() => move(index, -1)}
              onMoveDown={() => move(index, 1)}
              onEdit={
                section.isComputed
                  ? undefined
                  : () => setEditingIndex(index)
              }
              onRemove={section.type === "CURATED" ? () => removeCurated(index) : undefined}
            />
          ))}

          {/* ADDING A SECTION IS ADDING AN EMPTY ONE. It cannot be
              saved until it has a title and products -- the backend
              refuses it and so does the editor -- which is why these
              land you straight in the editor rather than quietly
              appending a broken row. */}
          <View style={styles.addRow}>
            {!hasFeatured && (
              <AddButton
                icon={<Star size={16} color={theme.colors.primary} strokeWidth={2.2} />}
                label="Add your pick"
                onPress={() => {
                  // STRAIGHT TO THE TOP. A pick that sits fourth is not
                  // a pick -- the whole reason it is one product shown
                  // large is that it is the first thing a business
                  // sees. It can still be moved afterwards; this is
                  // the sensible starting position, not a lock.
                  update([
                    {
                      type: "FEATURED_PRODUCT",
                      isEnabled: true,
                      position: 0,
                      isComputed: false,
                      title: null,
                      subtitle: null,
                      productIds: [],
                    },
                    ...draft,
                  ]);
                  setEditingIndex(0);
                }}
              />
            )}
            {curatedCount < MAX_CURATED_SECTIONS && (
              <AddButton
                icon={<Plus size={16} color={theme.colors.primary} strokeWidth={2.4} />}
                label="Add your own shelf"
                onPress={() => {
                  update([
                    ...draft,
                    {
                      type: "CURATED",
                      isEnabled: true,
                      position: draft.length,
                      isComputed: false,
                      title: "",
                      subtitle: null,
                      productIds: [],
                    },
                  ]);
                  setEditingIndex(draft.length);
                }}
              />
            )}
          </View>
        </View>
      </ScrollView>

      {/* THE SAVE BAR ONLY EXISTS WHEN THERE IS SOMETHING TO SAVE. A
          permanently-present button on an unedited screen invites a
          tap that does nothing, and on a screen whose edits are all
          local that is exactly the tap someone makes to check whether
          their changes took. */}
      <SectionEditorSheet
        visible={editingIndex !== null}
        section={editingIndex !== null ? (draft[editingIndex] ?? null) : null}
        onClose={() => {
          // BACKING OUT OF A SECTION THAT WAS NEVER FILLED IN removes
          // it again. "Add your own strip" appends an empty row and
          // opens the editor immediately, so cancelling there must not
          // leave a nameless, productless strip sitting in the list.
          const index = editingIndex;
          setEditingIndex(null);
          if (index === null) return;
          const section = draft[index];
          if (section && !section.isComputed && section.productIds.length === 0) {
            update(draft.filter((_, position) => position !== index));
          }
        }}
        onApply={(edited) => {
          const index = editingIndex;
          setEditingIndex(null);
          if (index === null) return;
          const next = [...draft];
          next[index] = edited;
          update(next);
        }}
      />

      {isDirty && (
        <View
          style={[
            styles.saveBar,
            { backgroundColor: theme.colors.surface, borderTopColor: theme.colors.outlineVariant },
          ]}
        >
          <PrimaryButton onPress={handleSave} loading={isSaving} disabled={isSaving}>
            Save storefront
          </PrimaryButton>
        </View>
      )}
    </ScreenContainer>
  );
}

function SectionRow({
  section,
  isFirst,
  isLast,
  onToggle,
  onMoveUp,
  onMoveDown,
  onEdit,
  onRemove,
}: {
  section: StorefrontConfigSection;
  isFirst: boolean;
  isLast: boolean;
  onToggle: (value: boolean) => void;
  onMoveUp: () => void;
  onMoveDown: () => void;
  onEdit?: () => void;
  onRemove?: () => void;
}) {
  const theme = useTheme();
  const copy = SECTION_COPY[section.type];
  const title = section.type === "CURATED" ? section.title || "Untitled shelf" : copy.title;

  return (
    <View
      style={[
        styles.row,
        { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant },
        !section.isEnabled && styles.rowDisabled,
      ]}
    >
      {/* ARROWS, NOT DRAG-AND-DROP. A long-press-and-drag inside a
          scrolling list fights the scroll on a phone, and two taps
          that always work beat a gesture that sometimes does. */}
      <View style={styles.reorder}>
        <Pressable
          onPress={onMoveUp}
          disabled={isFirst}
          hitSlop={6}
          style={[styles.arrow, isFirst && styles.arrowDisabled]}
          accessibilityRole="button"
          accessibilityLabel={`Move ${title} up`}
        >
          <ChevronUp size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2.4} />
        </Pressable>
        <Pressable
          onPress={onMoveDown}
          disabled={isLast}
          hitSlop={6}
          style={[styles.arrow, isLast && styles.arrowDisabled]}
          accessibilityRole="button"
          accessibilityLabel={`Move ${title} down`}
        >
          <ChevronDown size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2.4} />
        </Pressable>
      </View>

      <Pressable style={styles.rowBody} onPress={onEdit} disabled={!onEdit}>
        <Text style={[styles.rowTitle, { color: theme.colors.onSurface }]}>{title}</Text>
        <Text style={[styles.rowDescription, { color: theme.colors.onSurfaceVariant }]}>
          {copy.description}
        </Text>
        {!section.isComputed && (
          <Text style={[styles.rowMeta, { color: theme.colors.primary }]}>
            {section.productIds.length === 0
              ? "Choose products"
              : `${section.productIds.length} ${section.productIds.length === 1 ? "product" : "products"} · Edit`}
          </Text>
        )}
      </Pressable>

      <View style={styles.rowActions}>
        <Switch value={section.isEnabled} onValueChange={onToggle} />
        {onRemove && (
          <Pressable
            onPress={onRemove}
            hitSlop={8}
            accessibilityRole="button"
            accessibilityLabel={`Remove ${title}`}
          >
            <Trash2 size={18} color={theme.colors.error} strokeWidth={2} />
          </Pressable>
        )}
      </View>
    </View>
  );
}

function AddButton({
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
        styles.addButton,
        { borderColor: theme.colors.primary, opacity: pressed ? 0.7 : 1 },
      ]}
      accessibilityRole="button"
      accessibilityLabel={label}
    >
      {icon}
      <Text style={[styles.addLabel, { color: theme.colors.primary }]}>{label}</Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  content: { paddingBottom: spacing.xxl },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  body: { paddingHorizontal: spacing.md, paddingTop: spacing.sm, gap: spacing.sm },

  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    borderWidth: 1,
    borderRadius: radius.lg,
    padding: spacing.sm,
  },
  rowDisabled: { opacity: 0.55 },
  reorder: { gap: 2 },
  arrow: { padding: 2 },
  arrowDisabled: { opacity: 0.25 },
  rowBody: { flex: 1, gap: 2 },
  rowTitle: { ...typography.body, fontWeight: "700" },
  rowDescription: { ...typography.bodySmall, fontSize: 12, lineHeight: 17 },
  rowMeta: { ...typography.bodySmall, fontSize: 12, fontWeight: "700", marginTop: 2 },
  rowActions: { alignItems: "center", gap: spacing.sm },

  addRow: { gap: spacing.sm, marginTop: spacing.sm },
  addButton: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.xs,
    minHeight: 46,
    borderRadius: radius.lg,
    borderWidth: 1.5,
    borderStyle: "dashed",
  },
  addLabel: { ...typography.bodySmall, fontWeight: "700" },

  saveBar: { padding: spacing.md, borderTopWidth: StyleSheet.hairlineWidth },
});

import React, { useEffect, useState } from "react";
import { FlatList, Image, Modal, Pressable, StyleSheet, Text, View } from "react-native";
import { Check, Package, X } from "lucide-react-native";
import { TextInput, useTheme } from "react-native-paper";
import { useSafeAreaInsets } from "react-native-safe-area-context";

import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { formatCents } from "@/features/dashboard/supplier/products/services/productMapper";
import { useProducts } from "@/features/dashboard/supplier/products/hooks/useProducts";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import {
  MAX_SECTION_PRODUCTS,
  MAX_SUBTITLE_LENGTH,
  MIN_CURATED_PRODUCTS,
  type StorefrontConfigSection,
} from "../types";

/**
 * Editing one chosen section -- its title, and which products are in
 * it.
 *
 * A MODAL RATHER THAN A ROUTE, and that is a real decision. The
 * settings screen holds the whole storefront as an UNSAVED draft
 * (reordering is a sequence of moves, committed once). A separate
 * route would have to either receive that draft through navigation
 * params and hand it back, or keep it in a store two screens share --
 * both of which are machinery in service of nothing, since this editor
 * only ever edits the section the supplier just tapped.
 *
 * ITS OWN LOCAL COPY, applied on Done. Cancelling has to actually
 * cancel; editing the draft in place would leave a half-chosen product
 * list behind when someone backs out.
 *
 * ARCHIVED PRODUCTS ARE NOT OFFERED. The backend refuses them anyway
 * (a strip would silently drop them when a business looked), so the
 * supplier is stopped here rather than by a 422 after arranging
 * everything.
 */
export function SectionEditorSheet({
  section,
  visible,
  onClose,
  onApply,
}: {
  section: StorefrontConfigSection | null;
  visible: boolean;
  onClose: () => void;
  onApply: (section: StorefrontConfigSection) => void;
}) {
  const theme = useTheme();
  const insets = useSafeAreaInsets();
  const { products, isLoading } = useProducts();

  const [title, setTitle] = useState("");
  const [subtitle, setSubtitle] = useState("");
  const [selected, setSelected] = useState<string[]>([]);

  useEffect(() => {
    if (!section) return;
    setTitle(section.title ?? "");
    setSubtitle(section.subtitle ?? "");
    setSelected(section.productIds);
  }, [section]);

  if (!section) return null;

  const isFeatured = section.type === "FEATURED_PRODUCT";
  const sellable = (products ?? []).filter((product) => !product.isArchived);

  const toggle = (productId: string) => {
    // A FEATURED PICK IS ONE PRODUCT, so tapping another replaces it
    // rather than adding a second and failing validation later.
    if (isFeatured) {
      setSelected(selected[0] === productId ? [] : [productId]);
      return;
    }
    if (selected.includes(productId)) {
      setSelected(selected.filter((id) => id !== productId));
      return;
    }
    if (selected.length >= MAX_SECTION_PRODUCTS) return;
    setSelected([...selected, productId]);
  };

  const problem = isFeatured
    ? selected.length !== 1
      ? "Choose one product to feature."
      : null
    : !title.trim()
      ? "Give your shelf a name."
      : selected.length < MIN_CURATED_PRODUCTS
        ? `Pick at least ${MIN_CURATED_PRODUCTS} products.`
        : null;

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <View style={[styles.container, { backgroundColor: theme.colors.background, paddingTop: insets.top }]}>
        <View style={[styles.header, { borderBottomColor: theme.colors.outlineVariant }]}>
          <Pressable onPress={onClose} hitSlop={10} accessibilityRole="button" accessibilityLabel="Cancel">
            <X size={24} color={theme.colors.onSurface} strokeWidth={2.4} />
          </Pressable>
          <Text style={[styles.headerTitle, { color: theme.colors.onSurface }]}>
            {isFeatured ? "Your pick" : "Your own shelf"}
          </Text>
          <View style={styles.headerSpacer} />
        </View>

        {!isFeatured && (
          <View style={styles.titleField}>
            <TextInput
              mode="outlined"
              label="Shelf name"
              placeholder="Stock up for month-end"
              value={title}
              onChangeText={setTitle}
              maxLength={60}
              dense
            />
            <Text style={[styles.hint, { color: theme.colors.onSurfaceVariant }]}>
              Businesses see this as the heading above your products.
            </Text>

            {/* OPTIONAL, and it stays optional. A good shelf title
                often needs no explaining, and requiring a second line
                would only produce filler nobody reads. */}
            <TextInput
              mode="outlined"
              label="Second line (optional)"
              placeholder="What sells out first after payday"
              value={subtitle}
              onChangeText={setSubtitle}
              maxLength={MAX_SUBTITLE_LENGTH}
              dense
            />
          </View>
        )}

        <View style={styles.countRow}>
          <Text style={[styles.count, { color: theme.colors.onSurfaceVariant }]}>
            {isFeatured
              ? selected.length === 1
                ? "1 product chosen"
                : "Choose a product"
              : `${selected.length} of ${MAX_SECTION_PRODUCTS} chosen`}
          </Text>
        </View>

        <FlatList
          data={sellable}
          keyExtractor={(product) => product.id}
          contentContainerStyle={styles.list}
          ListEmptyComponent={
            <Text style={[styles.empty, { color: theme.colors.onSurfaceVariant }]}>
              {isLoading ? "Loading your products…" : "You have no products to choose from yet."}
            </Text>
          }
          renderItem={({ item }) => {
            const isSelected = selected.includes(item.id);
            const photo = item.images?.[0] ?? null;
            return (
              <Pressable
                onPress={() => toggle(item.id)}
                style={({ pressed }) => [
                  styles.productRow,
                  {
                    backgroundColor: theme.colors.surface,
                    borderColor: isSelected ? theme.colors.primary : theme.colors.outlineVariant,
                    opacity: pressed ? 0.85 : 1,
                  },
                ]}
                accessibilityRole="checkbox"
                accessibilityState={{ checked: isSelected }}
                accessibilityLabel={item.name}
              >
                <View style={[styles.thumb, { backgroundColor: theme.colors.surfaceVariant }]}>
                  {photo ? (
                    <Image source={{ uri: photo }} style={styles.thumbImage} resizeMode="contain" />
                  ) : (
                    <Package size={18} color={theme.colors.onSurfaceVariant} strokeWidth={1.6} />
                  )}
                </View>
                <View style={styles.productBody}>
                  <Text style={[styles.productName, { color: theme.colors.onSurface }]} numberOfLines={2}>
                    {item.name}
                  </Text>
                  <Text style={[styles.productPrice, { color: theme.colors.onSurfaceVariant }]}>
                    {formatCents(item.priceCents)}
                  </Text>
                </View>
                <View
                  style={[
                    styles.check,
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
          }}
        />

        <View
          style={[
            styles.footer,
            { backgroundColor: theme.colors.surface, borderTopColor: theme.colors.outlineVariant },
          ]}
        >
          {problem && (
            <Text style={[styles.problem, { color: theme.colors.onSurfaceVariant }]}>{problem}</Text>
          )}
          <PrimaryButton
            disabled={Boolean(problem)}
            onPress={() =>
              onApply({
              ...section,
              title: isFeatured ? null : title.trim(),
              subtitle: isFeatured ? null : subtitle.trim() || null,
              productIds: selected,
            })
            }
          >
            Done
          </PrimaryButton>
        </View>
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderBottomWidth: StyleSheet.hairlineWidth,
  },
  headerTitle: { ...typography.h2 },
  headerSpacer: { width: 24 },
  titleField: { paddingHorizontal: spacing.md, paddingTop: spacing.md, gap: spacing.xs },
  hint: { ...typography.bodySmall, fontSize: 12 },
  countRow: { paddingHorizontal: spacing.md, paddingTop: spacing.md },
  count: { ...typography.caption, fontWeight: "700", textTransform: "uppercase", letterSpacing: 0.5 },
  list: { padding: spacing.md, gap: spacing.sm },
  empty: { ...typography.bodySmall, textAlign: "center", paddingVertical: spacing.xl },
  productRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    borderWidth: 1.5,
    borderRadius: radius.md,
    padding: spacing.sm,
  },
  thumb: { width: 48, height: 48, borderRadius: radius.sm, alignItems: "center", justifyContent: "center" },
  thumbImage: { width: "100%", height: "100%" },
  productBody: { flex: 1, gap: 2 },
  productName: { ...typography.bodySmall, fontWeight: "600" },
  productPrice: { ...typography.bodySmall, fontSize: 12 },
  check: { width: 24, height: 24, borderRadius: 12, borderWidth: 2, alignItems: "center", justifyContent: "center" },
  footer: { padding: spacing.md, borderTopWidth: StyleSheet.hairlineWidth, gap: spacing.sm },
  problem: { ...typography.bodySmall, fontSize: 12, textAlign: "center" },
});

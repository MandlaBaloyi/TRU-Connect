/**
 * SelectFieldModal — a full-screen searchable single-select list.
 * Built once, used twice (CategoryPickerModal, UnitPickerModal) rather
 * than two near-identical components -- both pickers are structurally
 * the same thing (search a short controlled list, pick one), so the
 * difference between them is data, not behaviour.
 *
 * Local/instant filtering only, same discipline as ProductSearchBar --
 * the option list is already in memory (16 categories, 12 units), so
 * there's never a reason to hit the network for this.
 */

import React, { useMemo, useState } from "react";
import { FlatList, Modal, Pressable, StyleSheet, Text, TextInput, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Check, ChevronLeft } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Option<T extends string> {
  value: T;
  label: string;
}

interface Props<T extends string> {
  visible: boolean;
  title: string;
  options: Option<T>[];
  selectedValue: T;
  onSelect: (value: T) => void;
  onClose: () => void;
}

export function SelectFieldModal<T extends string>({
  visible,
  title,
  options,
  selectedValue,
  onSelect,
  onClose,
}: Props<T>) {
  const theme = useTheme();
  const [searchTerm, setSearchTerm] = useState("");

  const filteredOptions = useMemo(() => {
    const q = searchTerm.trim().toLowerCase();
    if (!q) return options;
    return options.filter((option) => option.label.toLowerCase().includes(q));
  }, [options, searchTerm]);

  const handleSelect = (value: T) => {
    onSelect(value);
    setSearchTerm("");
    onClose();
  };

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={onClose}>
      <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
        <View style={styles.header}>
          <Pressable onPress={onClose} hitSlop={12} accessibilityRole="button" accessibilityLabel="Close">
            <ChevronLeft size={26} color={theme.colors.onSurface} strokeWidth={2.8} />
          </Pressable>
          <Text style={[styles.title, { color: theme.colors.onSurface }]}>{title}</Text>
          <View style={{ width: 24 }} />
        </View>

        <View style={[styles.searchField, { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface }]}>
          <TextInput
            value={searchTerm}
            onChangeText={setSearchTerm}
            placeholder={`Search ${title.toLowerCase()}...`}
            placeholderTextColor={theme.colors.onSurfaceVariant}
            style={[styles.searchInput, { color: theme.colors.onSurface }]}
            autoCorrect={false}
            autoCapitalize="none"
          />
        </View>

        <FlatList
          data={filteredOptions}
          keyExtractor={(item) => item.value}
          renderItem={({ item }) => {
            const selected = item.value === selectedValue;
            return (
              <Pressable
                onPress={() => handleSelect(item.value)}
                style={styles.row}
                accessibilityRole="button"
                accessibilityState={{ selected }}
              >
                <Text style={[styles.rowLabel, { color: theme.colors.onSurface }]}>{item.label}</Text>
                {selected && <Check size={18} color={theme.colors.primary} strokeWidth={2.5} />}
              </Pressable>
            );
          }}
          ItemSeparatorComponent={() => <View style={[styles.separator, { backgroundColor: theme.colors.outline }]} />}
          ListEmptyComponent={
            <Text style={[styles.empty, { color: theme.colors.onSurfaceVariant }]}>No matches.</Text>
          }
          contentContainerStyle={styles.list}
        />
      </View>
    </Modal>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, paddingTop: spacing.xl },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.md,
  },
  title: { ...typography.h2, fontWeight: "700" },
  searchField: {
    flexDirection: "row",
    alignItems: "center",
    minHeight: 48,
    borderWidth: 1,
    borderRadius: radius.md,
    marginHorizontal: spacing.md,
    paddingHorizontal: spacing.md,
  },
  searchInput: { flex: 1, ...typography.body, paddingVertical: spacing.sm },
  list: { paddingHorizontal: spacing.md, paddingTop: spacing.sm, paddingBottom: spacing.xxl },
  row: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    minHeight: 48,
    paddingVertical: spacing.sm,
  },
  rowLabel: { ...typography.body },
  separator: { height: StyleSheet.hairlineWidth },
  empty: { ...typography.body, textAlign: "center", paddingTop: spacing.xl },
});

import React from "react";
import { Modal, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { Camera, Image as ImageIcon, Eye, Trash2 } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  visible: boolean;
  title: string;
  /** When true, "View photo" and "Remove photo" are shown. */
  hasImage: boolean;
  onView: () => void;
  onTakePhoto: () => void;
  onChooseFromGallery: () => void;
  onRemove: () => void;
  onClose: () => void;
}

/**
 * Bottom action sheet for a single image slot (profile photo / cover
 * photo). Replaces the old Alert.alert menu, which on Android silently
 * dropped the Cancel button once there were four options and gave no
 * "view full image" affordance at all.
 *
 * Follows the same Modal + backdrop + bottom-sheet pattern as
 * SortOptionsSheet / DeclineReasonSheet. Each action closes the sheet
 * first, then runs -- so the picker / viewer opens over a clean screen.
 */
export function ImageActionSheet({
  visible,
  title,
  hasImage,
  onView,
  onTakePhoto,
  onChooseFromGallery,
  onRemove,
  onClose,
}: Props) {
  const theme = useTheme();
  const insets = useSafeAreaInsets();

  const run = (action: () => void) => () => {
    onClose();
    // Let the sheet's dismiss animation start before the next surface
    // (native picker / full-screen viewer) takes over.
    setTimeout(action, 150);
  };

  return (
    <Modal visible={visible} animationType="slide" transparent onRequestClose={onClose}>
      <Pressable style={styles.backdrop} onPress={onClose}>
        <Pressable
          style={[
            styles.sheet,
            { backgroundColor: theme.colors.background, paddingBottom: spacing.sm + insets.bottom },
          ]}
          onPress={() => {}}
        >
          <View style={[styles.grabber, { backgroundColor: theme.colors.outlineVariant }]} />
          <Text style={[styles.title, { color: theme.colors.onSurface }]}>{title}</Text>

          {hasImage && (
            <Row
              icon={<Eye size={20} color={theme.colors.onSurface} strokeWidth={2} />}
              label="View photo"
              onPress={run(onView)}
            />
          )}
          <Row
            icon={<Camera size={20} color={theme.colors.onSurface} strokeWidth={2} />}
            label="Take photo"
            onPress={run(onTakePhoto)}
          />
          <Row
            icon={<ImageIcon size={20} color={theme.colors.onSurface} strokeWidth={2} />}
            label="Choose from gallery"
            onPress={run(onChooseFromGallery)}
          />
          {hasImage && (
            <Row
              icon={<Trash2 size={20} color={theme.colors.error} strokeWidth={2} />}
              label="Remove photo"
              tone="danger"
              onPress={run(onRemove)}
            />
          )}

          <Pressable
            onPress={onClose}
            style={[styles.cancel, { borderColor: theme.colors.outlineVariant }]}
            accessibilityRole="button"
            accessibilityLabel="Cancel"
          >
            <Text style={[styles.cancelLabel, { color: theme.colors.onSurface }]}>Cancel</Text>
          </Pressable>
        </Pressable>
      </Pressable>
    </Modal>
  );
}

function Row({
  icon,
  label,
  onPress,
  tone,
}: {
  icon: React.ReactNode;
  label: string;
  onPress: () => void;
  tone?: "danger";
}) {
  const theme = useTheme();
  return (
    <Pressable
      onPress={onPress}
      style={({ pressed }) => [styles.row, pressed && { backgroundColor: theme.colors.surfaceVariant }]}
      accessibilityRole="button"
      accessibilityLabel={label}
    >
      {icon}
      <Text
        style={[
          styles.rowLabel,
          { color: tone === "danger" ? theme.colors.error : theme.colors.onSurface },
        ]}
      >
        {label}
      </Text>
    </Pressable>
  );
}

const styles = StyleSheet.create({
  backdrop: { flex: 1, backgroundColor: "rgba(0,0,0,0.45)", justifyContent: "flex-end" },
  sheet: {
    borderTopLeftRadius: radius.lg,
    borderTopRightRadius: radius.lg,
    paddingHorizontal: spacing.md,
    paddingTop: spacing.sm,
  },
  grabber: { alignSelf: "center", width: 36, height: 4, borderRadius: 2, marginBottom: spacing.sm },
  title: { ...typography.bodySmall, fontWeight: "700", textTransform: "uppercase", letterSpacing: 0.5, marginBottom: spacing.xs, marginLeft: spacing.sm },
  row: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    minHeight: 52,
    paddingHorizontal: spacing.sm,
    borderRadius: radius.sm,
  },
  rowLabel: { ...typography.body, fontWeight: "500" },
  cancel: {
    marginTop: spacing.sm,
    minHeight: 48,
    borderRadius: radius.md,
    borderWidth: 1,
    alignItems: "center",
    justifyContent: "center",
  },
  cancelLabel: { ...typography.body, fontWeight: "700" },
});

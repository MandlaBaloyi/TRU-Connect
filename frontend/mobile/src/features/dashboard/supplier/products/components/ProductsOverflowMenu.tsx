/**
 * ProductsOverflowMenu — the "⋮" button in the Products screen's
 * native header. Owns its own open/closed state internally so the
 * screen only has to supply what each action actually DOES, not menu
 * plumbing. Uses react-native-paper's own Menu (already a dependency
 * throughout this app via useTheme), not a hand-rolled dropdown.
 *
 * Download Template/Download Guide call straight into bulk-products'
 * own downloadDocuments.ts -- reused, not duplicated, since that's
 * genuinely where those bundled files live. Cross-feature import, same
 * as the navigation shortcuts already on this screen; still no
 * bulk-edit logic in this file.
 */

import React, { useState } from "react";
import { Pressable, StyleSheet } from "react-native";
import { Menu, useTheme } from "react-native-paper";
import { ArrowUpDown, Download, FileSpreadsheet, FileText, MoreVertical } from "lucide-react-native";

import { spacing } from "@/theme/spacing";

interface Props {
  onExport: () => void;
  onSort: () => void;
  onDownloadTemplate: () => void;
  onDownloadGuide: () => void;
}

export function ProductsOverflowMenu({ onExport, onSort, onDownloadTemplate, onDownloadGuide }: Props) {
  const theme = useTheme();
  const [visible, setVisible] = useState(false);

  const runAndClose = (action: () => void) => {
    setVisible(false);
    action();
  };

  return (
    <Menu
      visible={visible}
      onDismiss={() => setVisible(false)}
      anchor={
        // Same size/weight/touch-target as Community's own "⋮"
        // (app/(dashboard)/supplier/(tabs)/community.tsx's rightIcon) --
        // strokeWidth 2.4, not lucide's thinner default, and the same
        // iconButton padding/margin AppHeader uses for every header
        // action, so this reads as the same control, not a lookalike.
        <Pressable
          onPress={() => setVisible(true)}
          hitSlop={10}
          style={styles.iconButton}
          accessibilityRole="button"
          accessibilityLabel="More options"
        >
          <MoreVertical size={20} color={theme.colors.onSurface} strokeWidth={2.4} />
        </Pressable>
      }
    >
      <Menu.Item
        onPress={() => runAndClose(onExport)}
        title="Export Products"
        leadingIcon={({ size, color }) => <Download size={size} color={color} strokeWidth={2} />}
      />
      <Menu.Item
        onPress={() => runAndClose(onSort)}
        title="Sort by"
        leadingIcon={({ size, color }) => <ArrowUpDown size={size} color={color} strokeWidth={2} />}
      />
      <Menu.Item
        onPress={() => runAndClose(onDownloadTemplate)}
        title="Download Template"
        leadingIcon={({ size, color }) => <FileSpreadsheet size={size} color={color} strokeWidth={2} />}
      />
      <Menu.Item
        onPress={() => runAndClose(onDownloadGuide)}
        title="Download Guide"
        leadingIcon={({ size, color }) => <FileText size={size} color={color} strokeWidth={2} />}
      />
    </Menu>
  );
}

const styles = StyleSheet.create({
  iconButton: { padding: spacing.xs, marginLeft: spacing.xs },
});

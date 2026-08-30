import React, { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { ChevronDown, ChevronUp } from "lucide-react-native";

import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  title: string;
  children: React.ReactNode;
  /** Product Codes, Shipping, and Returns all default to expanded,
   *  matching the majority behaviour in the real reference (Bash) --
   *  most sections start open, letting a business collapse what they
   *  don't need rather than starting collapsed and hiding real
   *  information behind an extra tap. */
  defaultExpanded?: boolean;
}

/**
 * Shared by Product Codes, Shipping, and Returns -- one real
 * expand/collapse implementation rather than three copies. "Product
 * details" (the renamed top section: Supplier, Name, Price, Discount,
 * Availability, Sold as) deliberately does NOT use this -- that
 * section stays always visible, no arrows, since it's the decision-
 * making information a business needs immediately, not something to
 * tuck away.
 */
export function AccordionSection({ title, children, defaultExpanded = true }: Props) {
  const theme = useTheme();
  const [expanded, setExpanded] = useState(defaultExpanded);

  return (
    <View>
      <Pressable
        onPress={() => setExpanded((prev) => !prev)}
        style={styles.header}
        accessibilityRole="button"
        accessibilityState={{ expanded }}
        accessibilityLabel={title}
      >
        <Text style={[styles.title, { color: theme.colors.onSurface }]}>{title}</Text>
        {expanded ? (
          <ChevronUp size={20} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
        ) : (
          <ChevronDown size={20} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
        )}
      </Pressable>
      {expanded && <View style={styles.content}>{children}</View>}
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: spacing.sm,
  },
  title: { ...typography.body, fontWeight: "700" },
  content: { paddingBottom: spacing.sm, gap: spacing.sm },
});

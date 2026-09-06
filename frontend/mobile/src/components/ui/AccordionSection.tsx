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
  /** Rendered between the title and the chevron -- an InfoHint, in
   *  practice. Its own Pressable, so tapping the ⓘ opens the
   *  explanation without also toggling the section. */
  titleAccessory?: React.ReactNode;
}

/**
 * Shared by the product screen's Product Codes / Shipping / Returns
 * and the brand profile's fulfilment terms -- one real expand/collapse
 * implementation rather than a copy per screen.
 *
 * MOVED HERE from my-suppliers/components once find-supplier needed it
 * too: my-suppliers depends on find-supplier, not the reverse, so
 * importing it the other way would have pointed that arrow backwards.
 * Neutral ground, same reasoning as services/contact/contactLinks.ts.
 *
 * NOT EVERYTHING SHOULD COLLAPSE. The product screen's "Product
 * details" (Supplier, Name, Price, Discount, Availability, Sold as)
 * deliberately does NOT use this -- that's the decision-making
 * information a business needs immediately, not something to tuck
 * behind a tap. Use this for supporting detail, never for the answer
 * the screen exists to give.
 */
export function AccordionSection({ title, children, defaultExpanded = true, titleAccessory }: Props) {
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
        <View style={styles.titleRow}>
          <Text style={[styles.title, { color: theme.colors.onSurface }]}>{title}</Text>
          {titleAccessory}
        </View>
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
  titleRow: { flexDirection: "row", alignItems: "center", gap: spacing.xs, flexShrink: 1 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: spacing.sm,
  },
  title: { ...typography.body, fontWeight: "700" },
  content: { paddingBottom: spacing.sm, gap: spacing.sm },
});

import React from "react";
import { Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { ChevronRight } from "lucide-react-native";

import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import type { FeedPromo } from "../../types";

/**
 * A full-width promotional card in the feed.
 *
 * QUIET BY DESIGN, and this is a deliberate departure from the apps
 * this screen takes its shape from, where promos are the loudest thing
 * on the page. This is a working tool a spaza owner opens to place a
 * stock order, not a place to browse for entertainment: a promo that
 * out-shouts "Buy it again" is actively getting in the way of the job.
 * Surface background, hairline border, one line of colour on the
 * action -- the same card language as the rest of the app.
 *
 * THE HREF IS VALIDATED BEFORE IT IS FOLLOWED. Feed content is
 * server-supplied, and a route string from a payload is the obvious
 * place for something to go wrong later -- an external URL, or a deep
 * link into a screen this user has no business on. The card only ever
 * navigates to in-app business routes; anything else is dropped and
 * the card renders as plain, unpressable content.
 */
export function PromoCard({ promo, onPress }: { promo: FeedPromo; onPress: (href: string) => void }) {
  const theme = useTheme();
  const href = safeInAppHref(promo.href);

  const content = (
    <View
      style={[
        styles.card,
        { backgroundColor: theme.colors.surface, borderColor: theme.colors.outlineVariant },
      ]}
    >
      {promo.imageUrl ? (
        <Image source={{ uri: promo.imageUrl }} style={styles.image} resizeMode="cover" />
      ) : null}
      <View style={styles.body}>
        <Text style={[styles.title, { color: theme.colors.onSurface }]}>{promo.title}</Text>
        {promo.body ? (
          <Text style={[styles.text, { color: theme.colors.onSurfaceVariant }]}>{promo.body}</Text>
        ) : null}
      </View>
      {href ? <ChevronRight size={20} color={theme.colors.primary} strokeWidth={2.4} /> : null}
    </View>
  );

  if (!href) return <View style={styles.wrap}>{content}</View>;

  return (
    <Pressable
      onPress={() => onPress(href)}
      style={({ pressed }) => [styles.wrap, { opacity: pressed ? 0.85 : 1 }]}
      accessibilityRole="button"
      accessibilityLabel={promo.title}
    >
      {content}
    </Pressable>
  );
}

/** In-app business routes only. Never an external URL, never another
 *  role's dashboard -- see the docstring above on why a route string
 *  arriving from a server payload is not trusted as-is. */
function safeInAppHref(href: string | null): string | null {
  if (!href) return null;
  return href.startsWith("/business/") ? href : null;
}

const styles = StyleSheet.create({
  wrap: { paddingHorizontal: spacing.md },
  card: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.md,
    padding: spacing.md,
    borderRadius: radius.lg,
    borderWidth: 1,
  },
  image: { width: 56, height: 56, borderRadius: radius.md },
  body: { flex: 1, gap: 2 },
  title: { ...typography.body, fontWeight: "700" },
  text: { ...typography.bodySmall, lineHeight: 18 },
});

import React from "react";
import { View, StyleSheet } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { MoreVertical } from "lucide-react-native";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { AppHeader } from "@/components/navigation/AppHeader";
import { FeatureTile } from "@/components/cards/FeatureTile";
import { LoanBookIcon } from "@/features/dashboard/business/loan-book/components/LoanBookIcon";
import { OrderBookIcon } from "@/features/dashboard/business/order-book/components/OrderBookIcon";
import { spacing } from "@/theme/spacing";
import { useGridColumnWidth } from "@/hooks/useGridColumnWidth";

/**
 * Business Account tab — the business OPERATIONS area. "Which business
 * tool do I need?" Loan Book and Order Book are two separate tools on
 * purpose (different problems: money owed vs orders placed) — never
 * merge them. This tab is NOT for personal account settings; that
 * lives under More.
 *
 * NO "More to come" PLACEHOLDER — removed per direct feedback. Only
 * real tiles with a real business function belong here.
 *
 * ROUTE PATHS INCLUDE "business" ON PURPOSE.
 * In Expo Router, (parenthesised) folders are GROUPS and vanish from the
 * URL, but PLAIN folders are real segments and must appear in it. The
 * route lives at:
 *
 *     app/(dashboard)/business/loan-book/index.tsx
 *          └ group ┘  └ real ┘  └ real ┘
 *
 * so the URL is "/business/loan-book" — NOT "/loan-book", which resolves
 * to nothing and renders Expo's "Unmatched Route" screen. The same
 * applies to the supplier tab's own tiles.
 */
export default function BusinessAccount() {
  const router = useRouter();
  const theme = useTheme();
  // THE REAL FIX for a genuine, confirmed bug -- see
  // useGridColumnWidth's own docstring. 3 columns, matching the same
  // "5-9 core features" scale this whole grid needs to support going
  // forward, not just however many tiles happen to exist today.
  const tileWidth = useGridColumnWidth(3, spacing.md, spacing.md);

  return (
    <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
      <AppHeader
        variant="title"
        title="Account"
        subtitle="Your business tools"
        rightIcon={<MoreVertical size={20} color={theme.colors.onSurface} strokeWidth={2.4} />}
      />
      <View style={styles.grid}>
        <View style={{ width: tileWidth }}>
          <FeatureTile
            label="Loan Book"
            icon={<LoanBookIcon size={40} />}
            onPress={() => router.push("/business/loan-book")}
          />
        </View>

        <View style={{ width: tileWidth }}>
          <FeatureTile
            label="Order Book"
            icon={<OrderBookIcon size={40} />}
            onPress={() => router.push("/business/order-book")}
          />
        </View>

        {/* Future Account tiles go here — only added when they provide
            a clear business function, never just to fill the grid. */}
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.md,
    padding: spacing.md,
  },
});

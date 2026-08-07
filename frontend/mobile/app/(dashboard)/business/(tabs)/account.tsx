import React from "react";
import { View, StyleSheet } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { FeatureTile } from "@/components/cards/FeatureTile";
import { LoanBookIcon } from "@/features/dashboard/business/loan-book/components/LoanBookIcon";
import { OrderBookIcon } from "@/features/dashboard/business/order-book/components/OrderBookIcon";
import { BRAND_TOP_BAR_HEIGHT } from "@/components/navigation/BrandTopBar";
import { spacing } from "@/theme/spacing";

/**
 * Business Account tab — the feature launcher.
 *
 * Mirrors the supplier Account tab: a wrapping grid of FeatureTiles,
 * each 31% wide, icon above label. Reusing that pattern rather than
 * inventing a parallel one means both roles feel like the same app.
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
  const insets = useSafeAreaInsets();

  return (
    <ScreenContainer>
      <View style={[styles.grid, { paddingTop: insets.top + BRAND_TOP_BAR_HEIGHT + spacing.md }]}>
        <View style={styles.tileWrapper}>
          <FeatureTile
            label="Loan Book"
            icon={<LoanBookIcon size={40} />}
            onPress={() => router.push("/business/loan-book")}
          />
        </View>

        <View style={styles.tileWrapper}>
          <FeatureTile
            label="Order Book"
            icon={<OrderBookIcon size={40} />}
            onPress={() => router.push("/business/order-book")}
          />
        </View>

        {/* Future Account tiles go here */}
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
  tileWrapper: {
    width: "31%",
  },
});

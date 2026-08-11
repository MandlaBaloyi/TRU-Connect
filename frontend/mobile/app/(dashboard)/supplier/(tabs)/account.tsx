import React from "react";
import { View, StyleSheet } from "react-native";
import { useRouter } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { AppHeader } from "@/components/navigation/AppHeader";
import { FeatureTile } from "@/components/cards/FeatureTile";
import { ProductCatalogueIcon } from "@/features/dashboard/supplier/product-catalogue/components/ProductCatalogueIcon";
import { spacing } from "@/theme/spacing";

/** Supplier Account tab — same architecture as Business's Account
 *  (contextual header + tile grid), existing Product Catalogue tile
 *  kept as-is. */
export default function SupplierAccount() {
  const router = useRouter();

  return (
    <ScreenContainer paddingHorizontal={0} edges={["bottom", "left", "right"]}>
      <AppHeader variant="title" title="Account" subtitle="Your business tools" />
      <View style={styles.grid}>
        <View style={styles.tileWrapper}>
          <FeatureTile
            label="Product Catalogue"
            icon={<ProductCatalogueIcon size={40} />}
            onPress={() => router.push("/product-catalogue")}
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

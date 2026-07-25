import React from "react";
import { View, StyleSheet } from "react-native";
import { useRouter } from "expo-router";
import { useSafeAreaInsets } from "react-native-safe-area-context";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { FeatureTile } from "@/components/cards/FeatureTile";
import { ProductCatalogueIcon } from "@/features/dashboard/supplier/product-catalogue/components/ProductCatalogueIcon";
import { BRAND_TOP_BAR_HEIGHT } from "@/components/navigation/BrandTopBar";
import { spacing } from "@/theme/spacing";

export default function SupplierAccount() {
  const router = useRouter();
  const insets = useSafeAreaInsets();

  return (
    <ScreenContainer>
      <View style={[styles.grid, { paddingTop: insets.top + BRAND_TOP_BAR_HEIGHT + spacing.md }]}>
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
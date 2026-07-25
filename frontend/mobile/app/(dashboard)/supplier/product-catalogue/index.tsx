import React from "react";
import { useRouter } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ScreenHeader } from "@/components/navigation/ScreenHeader";
import { ProductCatalogueScreen } from "@/features/dashboard/supplier/product-catalogue/screens/ProductCatalogueScreen";

export default function ProductCatalogueRoute() {
  const router = useRouter();
  return (
    <ScreenContainer>
      <ScreenHeader title="Product Catalogue" onBack={() => router.back()} />
      <ProductCatalogueScreen />
    </ScreenContainer>
  );
}
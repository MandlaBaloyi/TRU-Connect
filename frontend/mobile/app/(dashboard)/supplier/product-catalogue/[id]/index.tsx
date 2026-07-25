import React from "react";
import { useRouter } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ScreenHeader } from "@/components/navigation/ScreenHeader";
import { ProductDetailsScreen } from "@/features/dashboard/supplier/product-catalogue/screens/ProductDetailsScreen";

export default function ProductDetailsRoute() {
  const router = useRouter();
  return (
    <ScreenContainer>
      <ScreenHeader title="Product Details" onBack={() => router.back()} />
      <ProductDetailsScreen />
    </ScreenContainer>
  );
}
import React from "react";
import { useRouter } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ScreenHeader } from "@/components/navigation/ScreenHeader";
import { ProductImagesScreen } from "@/features/dashboard/supplier/product-catalogue/screens/ProductImagesScreen";

export default function ProductImagesRoute() {
  const router = useRouter();
  return (
    <ScreenContainer>
      <ScreenHeader title="Product Images" onBack={() => router.back()} />
      <ProductImagesScreen />
    </ScreenContainer>
  );
}
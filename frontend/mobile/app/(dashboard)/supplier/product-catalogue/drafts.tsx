import React from "react";
import { useRouter } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ScreenHeader } from "@/components/navigation/ScreenHeader";
import { DraftProductsScreen } from "@/features/dashboard/supplier/product-catalogue/screens/DraftProductsScreen";

export default function DraftProductsRoute() {
  const router = useRouter();
  return (
    <ScreenContainer>
      <ScreenHeader title="Draft Products" onBack={() => router.back()} />
      <DraftProductsScreen />
    </ScreenContainer>
  );
}
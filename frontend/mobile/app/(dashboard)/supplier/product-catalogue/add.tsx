import React from "react";
import { useRouter } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ScreenHeader } from "@/components/navigation/ScreenHeader";
import { AddProductScreen } from "@/features/dashboard/supplier/product-catalogue/screens/AddProductScreen";

export default function AddProductRoute() {
  const router = useRouter();
  return (
    <ScreenContainer>
      <ScreenHeader title="Add Product" onBack={() => router.back()} />
      <AddProductScreen />
    </ScreenContainer>
  );
}
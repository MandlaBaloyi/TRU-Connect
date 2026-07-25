import React from "react";
import { useRouter } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { ScreenHeader } from "@/components/navigation/ScreenHeader";
import { EditProductScreen } from "@/features/dashboard/supplier/product-catalogue/screens/EditProductScreen";

export default function EditProductRoute() {
  const router = useRouter();
  return (
    <ScreenContainer>
      <ScreenHeader title="Edit Product" onBack={() => router.back()} />
      <EditProductScreen />
    </ScreenContainer>
  );
}
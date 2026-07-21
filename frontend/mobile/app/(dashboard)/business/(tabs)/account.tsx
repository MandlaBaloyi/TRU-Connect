import React from "react";
import { StyleSheet } from "react-native";
import { useRouter } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { SectionHeader } from "@/features/dashboard/shared/components/SectionHeader";

export default function BusinessAccount() {
  const router = useRouter();

  return (
    <ScreenContainer>
      <SectionHeader
        title="Account"
        onClosePress={() => router.push("/(dashboard)/business/(tabs)/home")}
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({});
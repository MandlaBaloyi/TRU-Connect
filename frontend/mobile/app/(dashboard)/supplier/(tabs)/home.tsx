import React from "react";
import { StyleSheet } from "react-native";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { HomeHeader } from "@/features/dashboard/shared/components/HomeHeader";

export default function SupplierDashboardHome() {
  return (
    <ScreenContainer>
      <HomeHeader
        greeting="Good Morning"
        name="Supplier Name"
        avatarLabel="SN"
        unreadNotificationCount={0}
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({});
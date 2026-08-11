import React from "react";
import { Stack } from "expo-router";
import { useTheme } from "react-native-paper";

/**
 * THIS FILE DID NOT EXIST BEFORE -- that was the real bug.
 *
 * business/ contains (tabs) (Home/Account/Community/Discovery/More)
 * as ONE sibling, and loan-book/, order-book/, settings/, my-business/,
 * my-account/, security/ as OTHER siblings, each its own separate
 * Stack navigator. Something has to manage the transition BETWEEN
 * those siblings -- e.g. tapping "Loan Book" on the Account tab
 * navigates from the (tabs) navigator into the loan-book Stack. With
 * no _layout.tsx here, Expo Router silently used its own default,
 * UNSTYLED Stack for exactly that transition -- which defaults
 * contentStyle to plain white. That's the real, confirmed root cause
 * of "Account -> tap Loan Book -> white flash -> Loan Book appears"
 * (and the same for Order Book, Settings, My Business, My Account,
 * Security): every one of those crosses this exact, previously
 * unstyled layer.
 */
export default function BusinessSectionLayout() {
  const theme = useTheme();
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: theme.colors.background },
      }}
    />
  );
}

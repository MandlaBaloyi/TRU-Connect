import React from "react";
import { ViewStyle } from "react-native";
import { SafeAreaView, Edge } from "react-native-safe-area-context";
import { useTheme } from "react-native-paper";

interface SafeAreaScreenProps {
  children: React.ReactNode;
  style?: ViewStyle;
  edges?: Edge[];
}

/**
 * Bare safe-area + themed background primitive. ScreenContainer builds on
 * top of this with standard horizontal padding conventions -- composition
 * over duplication, per the master prompt's Development Principles.
 */
export function SafeAreaScreen({ children, style, edges }: SafeAreaScreenProps) {
  const theme = useTheme();
  return (
    <SafeAreaView
      edges={edges}
      style={[{ flex: 1, backgroundColor: theme.colors.background }, style]}
    >
      {children}
    </SafeAreaView>
  );
}

import { Stack } from "expo-router";

/**
 * Business Profile Setup (Multi-step Wizard) layout.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 7, Steps 1-5).
 */
export default function ProfileSetupLayout() {
  return <Stack screenOptions={{ headerShown: false, gestureEnabled: false }} />;
}

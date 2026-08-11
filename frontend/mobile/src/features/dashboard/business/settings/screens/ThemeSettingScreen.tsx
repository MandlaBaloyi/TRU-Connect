import React from "react";
import { useTheme } from "react-native-paper";
import { Smartphone, Sun, Moon, Palette } from "lucide-react-native";
import { OptionPickerScreen } from "@/features/dashboard/business/settings/components/OptionPickerScreen";
import { useSettings } from "@/features/dashboard/business/settings/hooks/SettingsProvider";
import type { ThemePreference } from "@/features/dashboard/business/settings/types";

/** REAL — changes the theme across the ENTIRE app immediately (see
 *  ThemeProvider, which reads this preference). */
export default function ThemeSettingScreen() {
  const { settings, updateSettings } = useSettings();
  const theme = useTheme();

  return (
    <OptionPickerScreen<ThemePreference>
      hero={{
        icon: <Palette size={28} color={theme.colors.primary} strokeWidth={1.8} />,
        title: "Theme",
        description: "Choose how TruConnect looks. This applies across the whole app, everywhere you go.",
      }}
      options={[
        {
          value: "SYSTEM",
          label: "System default",
          description: "Match your device's appearance automatically",
          icon: (color) => <Smartphone size={20} color={color} />,
        },
        {
          value: "LIGHT",
          label: "Light",
          description: "A bright, high-contrast look",
          icon: (color) => <Sun size={20} color={color} />,
        },
        {
          value: "DARK",
          label: "Dark",
          description: "Easier on the eyes in low light",
          icon: (color) => <Moon size={20} color={color} />,
        },
      ]}
      selected={settings.theme}
      onSelect={(themeValue) => updateSettings({ theme: themeValue })}
    />
  );
}

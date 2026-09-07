import React from "react";
import { useTheme } from "react-native-paper";
import { Globe, Languages } from "lucide-react-native";
import { OptionPickerScreen } from "@/features/dashboard/shared/settings/components/OptionPickerScreen";
import { useSettings } from "@/features/dashboard/shared/settings/hooks/SettingsProvider";
import { PLANNED_LANGUAGES, type LanguagePreference } from "@/features/dashboard/shared/settings/types";

/**
 * REAL (frontend architecture) — the preference genuinely persists,
 * but only English is offered as selectable because no other
 * translations exist yet. All 10 of South Africa's other official
 * languages are listed honestly as planned rather than offered as
 * selectable-but-inert, which would be exactly the kind of fake
 * control this feature avoids.
 */
export default function LanguageSettingScreen() {
  const { settings, updateSettings } = useSettings();
  const theme = useTheme();
  return (
    <OptionPickerScreen<LanguagePreference>
      hero={{
        icon: <Languages size={28} color={theme.colors.primary} strokeWidth={1.8} />,
        title: "Language",
        description: "Choose the language TruConnect uses throughout the app.",
      }}
      options={[
        {
          value: "EN",
          label: "English",
          description: "Available now",
          icon: (color) => <Globe size={20} color={color} />,
        },
      ]}
      selected={settings.language}
      onSelect={(language) => updateSettings({ language })}
      unavailableOptions={PLANNED_LANGUAGES}
      unavailableSectionLabel="South Africa's other official languages — coming soon"
      footnote="TruConnect is built to support all 11 of South Africa's official languages. Each one will be added with a full, proper translation rather than a partial one."
    />
  );
}

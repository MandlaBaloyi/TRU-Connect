import React from "react";
import { useTheme } from "react-native-paper";
import { Home, LayoutGrid, Users, Compass, MoreHorizontal, Rocket } from "lucide-react-native";
import { OptionPickerScreen } from "@/features/dashboard/shared/settings/components/OptionPickerScreen";
import { useSettings } from "@/features/dashboard/shared/settings/hooks/SettingsProvider";
import { START_SCREEN_LABELS, type StartScreenPreference } from "@/features/dashboard/shared/settings/types";

const ICONS: Record<StartScreenPreference, (color: string) => React.ReactNode> = {
  HOME: (c) => <Home size={20} color={c} />,
  ACCOUNT: (c) => <LayoutGrid size={20} color={c} />,
  COMMUNITY: (c) => <Users size={20} color={c} />,
  DISCOVERY: (c) => <Compass size={20} color={c} />,
  MORE: (c) => <MoreHorizontal size={20} color={c} />,
};

/** REAL — persists the choice.
 *
 *  Shared by both roles: business and supplier have the identical five
 *  bottom tabs, so the preference means the same thing either way (see
 *  StartScreenPreference's own note, including the bug where this
 *  offered Loan Book and Order Book — tools, not tabs). */
export default function StartScreenSettingScreen() {
  const { settings, updateSettings } = useSettings();
  const theme = useTheme();
  const options = (Object.keys(START_SCREEN_LABELS) as StartScreenPreference[]).map((value) => ({
    value,
    label: START_SCREEN_LABELS[value],
    icon: ICONS[value],
  }));

  return (
    <OptionPickerScreen<StartScreenPreference>
      hero={{
        icon: <Rocket size={28} color={theme.colors.primary} strokeWidth={1.8} />,
        title: "Default start screen",
        description: "Choose which screen TruConnect opens on when you sign in.",
      }}
      options={options}
      selected={settings.startScreen}
      onSelect={(startScreen) => updateSettings({ startScreen })}
      footnote="TruConnect will open on this screen when you sign in."
    />
  );
}

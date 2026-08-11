import React from "react";
import { useTheme } from "react-native-paper";
import { Home, LayoutGrid, BookOpen, ClipboardList, Users, Compass, Rocket } from "lucide-react-native";
import { OptionPickerScreen } from "@/features/dashboard/business/settings/components/OptionPickerScreen";
import { useSettings } from "@/features/dashboard/business/settings/hooks/SettingsProvider";
import { START_SCREEN_LABELS, type StartScreenPreference } from "@/features/dashboard/business/settings/types";

const ICONS: Record<StartScreenPreference, (color: string) => React.ReactNode> = {
  HOME: (c) => <Home size={20} color={c} />,
  ACCOUNT: (c) => <LayoutGrid size={20} color={c} />,
  LOAN_BOOK: (c) => <BookOpen size={20} color={c} />,
  ORDER_BOOK: (c) => <ClipboardList size={20} color={c} />,
  COMMUNITY: (c) => <Users size={20} color={c} />,
  DISCOVERY: (c) => <Compass size={20} color={c} />,
};

/** REAL — persists the choice. A business owner who lives in Order
 *  Book all day shouldn't be routed through Home every time. */
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

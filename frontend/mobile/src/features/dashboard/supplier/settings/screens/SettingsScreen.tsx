import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import Constants from "expo-constants";
import {
  Sun,
  Package,
  Users,
  Bell,
  Languages,
  Home,
  ShieldQuestion,
  ClipboardList,
  RefreshCw,
  Smartphone,
  WifiOff,
  Database,
  Eye,
  Compass,
  BarChart3,
  Sparkles,
  HelpCircle,
  MessageSquareWarning,
  ScrollText,
  FileText,
  Info,
} from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { CardSection, Card, SwitchCard } from "@/components/lists/CardListUI";
import { useSettings } from "@/features/dashboard/shared/settings/hooks/SettingsProvider";
import { LANGUAGE_LABELS, START_SCREEN_LABELS, THEME_LABELS } from "@/features/dashboard/shared/settings/types";
import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * Settings — supplier side.
 *
 * A SEPARATE MENU FROM THE BUSINESS ONE, deliberately. The two roles
 * share almost everything a setting DOES — theme, language, offline
 * mode, storage, help, legal — and all of that now lives once in
 * shared/settings/ and is rendered for both roles. What they don't
 * share is what a setting is ABOUT. A business configures how it buys
 * stock and how it appears as a buyer; a supplier configures how it
 * receives orders and how its shopfront appears to buyers. Merging the
 * two menus would give every reader a screen half full of rows that
 * don't apply to them.
 *
 * So the split is: shared machinery and shared device-level screens,
 * role-specific menus and role-specific privacy screens.
 *
 * Every row here is honestly one of three things (see SettingStatus in
 * shared/settings/types.ts): a REAL setting that changes app behaviour
 * today, an INFORMATIONAL screen describing a capability that
 * genuinely exists, or a COMING_SOON entry that navigates to an
 * explanation. There are deliberately NO switches on rows whose
 * infrastructure isn't built — "Confirm before deleting" is the only
 * switch here, because it's the only boolean that does something
 * today.
 *
 * The supplier visibility toggles that DO work today (photo
 * visibility, contact sharing, activity status, track record) still
 * live on the supplier profile. They move into the Privacy &
 * visibility section below once this shell has been reviewed — a
 * profile holds the input details, not the switches that govern who
 * gets to see them.
 */
export default function SupplierSettingsScreen() {
  const theme = useTheme();
  const router = useRouter();
  const { settings, updateSettings } = useSettings();

  const go = (path: string) => () => router.push(path as any);

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        <CardSection title="Appearance">
          <Card
            icon={(c) => <Sun size={20} color={c} />}
            label="Theme"
            description={THEME_LABELS[settings.theme]}
            onPress={go("/supplier/settings/theme")}
          />
        </CardSection>

        {/* A supplier RECEIVES orders rather than places them, so the
            order row is worded from that side. Discovery notifications
            have no supplier equivalent yet — a supplier is the thing
            being discovered, not the one browsing — so that row is
            absent rather than present and meaningless. */}
        <CardSection title="Notifications">
          <Card icon={(c) => <Package size={20} color={c} />} label="Incoming order notifications" onPress={go("/supplier/settings/notifications-orders")} />
          <Card icon={(c) => <Users size={20} color={c} />} label="Community activity" onPress={go("/supplier/settings/notifications-community")} />
          <Card icon={(c) => <Bell size={20} color={c} />} label="TruConnect announcements" onPress={go("/supplier/settings/notifications-announcements")} />
        </CardSection>

        <CardSection title="Supplier experience">
          <Card
            icon={(c) => <Languages size={20} color={c} />}
            label="Language"
            description={LANGUAGE_LABELS[settings.language]}
            onPress={go("/supplier/settings/language")}
          />
          <Card
            icon={(c) => <Home size={20} color={c} />}
            label="Default start screen"
            description={START_SCREEN_LABELS[settings.startScreen]}
            onPress={go("/supplier/settings/start-screen")}
          />
          <SwitchCard
            icon={(c) => <ShieldQuestion size={20} color={c} />}
            label="Confirm before deleting"
            description="Ask before removing products, orders or entries."
            value={settings.confirmBeforeDeleting}
            onValueChange={(confirmBeforeDeleting) => updateSettings({ confirmBeforeDeleting })}
          />
          <Card icon={(c) => <ClipboardList size={20} color={c} />} label="Order handling preferences" onPress={go("/supplier/settings/preferences")} />
        </CardSection>

        <CardSection title="Data & connectivity">
          <Card icon={(c) => <RefreshCw size={20} color={c} />} label="Sync" onPress={go("/supplier/settings/sync")} />
          <Card icon={(c) => <Smartphone size={20} color={c} />} label="Mobile data usage" onPress={go("/supplier/settings/mobile-data")} />
          <Card icon={(c) => <WifiOff size={20} color={c} />} label="Offline mode" onPress={go("/supplier/settings/offline-mode")} />
          <Card icon={(c) => <Database size={20} color={c} />} label="Storage & cache" onPress={go("/supplier/settings/storage")} />
        </CardSection>

        {/* The supplier-specific half. The business menu asks one
            question here — who can find me as a buyer. A supplier is
            asking three separate ones instead: how the shopfront looks
            to a connected buyer, what the community sees of their
            activity, and whether they surface in Discovery at all. */}
        <CardSection title="Privacy & visibility">
          <Card icon={(c) => <Eye size={20} color={c} />} label="Supplier visibility" onPress={go("/supplier/settings/supplier-visibility")} />
          <Card icon={(c) => <Users size={20} color={c} />} label="Community activity" onPress={go("/supplier/settings/community-activity")} />
          <Card icon={(c) => <Compass size={20} color={c} />} label="Discovery visibility" onPress={go("/supplier/settings/discovery-visibility")} />
          <Card icon={(c) => <BarChart3 size={20} color={c} />} label="Data usage" onPress={go("/supplier/settings/data-usage")} />
          <Card icon={(c) => <Sparkles size={20} color={c} />} label="Personalisation" onPress={go("/supplier/settings/personalisation")} />
        </CardSection>

        <CardSection title="Support & information">
          <Card icon={(c) => <HelpCircle size={20} color={c} />} label="Help & support" onPress={go("/supplier/settings/help")} />
          <Card icon={(c) => <MessageSquareWarning size={20} color={c} />} label="Report a problem" onPress={go("/supplier/settings/report-problem")} />
          <Card icon={(c) => <ScrollText size={20} color={c} />} label="Privacy policy" onPress={go("/supplier/settings/privacy-policy")} />
          <Card icon={(c) => <FileText size={20} color={c} />} label="Terms of service" onPress={go("/supplier/settings/terms")} />
          <Card icon={(c) => <Info size={20} color={c} />} label="About TruConnect" onPress={go("/supplier/settings/about")} />
        </CardSection>

        <View style={styles.versionWrap}>
          <Text style={[styles.version, { color: theme.colors.onSurfaceVariant }]}>
            Version {Constants.expoConfig?.version ?? "1.0.0"}
          </Text>
        </View>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.xl },
  versionWrap: { alignItems: "center", paddingTop: spacing.sm },
  version: { ...typography.bodySmall, fontWeight: "600" },
});

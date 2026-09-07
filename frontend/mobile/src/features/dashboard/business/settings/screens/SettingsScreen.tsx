import React from "react";
import { ScrollView, StyleSheet, Text, View } from "react-native";
import { useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import Constants from "expo-constants";
import {
  Palette,
  Bell,
  Briefcase,
  Wifi,
  Lock,
  LifeBuoy,
  Sun,
  Languages,
  Home,
  ShieldQuestion,
  Package,
  RefreshCw,
  Smartphone,
  WifiOff,
  Database,
  Eye,
  Users,
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
 * Settings — redesigned onto the shared card system (see
 * src/components/lists/CardListUI.tsx), the same visual language as
 * Account Security: rounded cards with icons instead of a flat
 * divided list.
 *
 * Every row here is honestly one of three things (see types.ts's
 * SettingStatus): a REAL setting that changes app behaviour today, an
 * INFORMATIONAL screen describing a capability that genuinely exists,
 * or a COMING_SOON entry that navigates to an explanation. There are
 * deliberately NO switches on rows whose infrastructure isn't built —
 * "Confirm before deleting" is the only switch on this screen, because
 * it's the only boolean setting that actually does something today.
 */
export default function SettingsScreen() {
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
            onPress={go("/business/settings/theme")}
          />
        </CardSection>

        <CardSection title="Notifications">
          <Card icon={(c) => <Package size={20} color={c} />} label="Stock order notifications" onPress={go("/business/settings/notifications-orders")} />
          <Card icon={(c) => <Users size={20} color={c} />} label="Community activity" onPress={go("/business/settings/notifications-community")} />
          <Card icon={(c) => <Sparkles size={20} color={c} />} label="Discovery & opportunities" onPress={go("/business/settings/notifications-discovery")} />
          <Card icon={(c) => <Bell size={20} color={c} />} label="TruConnect announcements" onPress={go("/business/settings/notifications-announcements")} />
        </CardSection>

        <CardSection title="Business experience">
          <Card
            icon={(c) => <Languages size={20} color={c} />}
            label="Language"
            description={LANGUAGE_LABELS[settings.language]}
            onPress={go("/business/settings/language")}
          />
          <Card
            icon={(c) => <Home size={20} color={c} />}
            label="Default start screen"
            description={START_SCREEN_LABELS[settings.startScreen]}
            onPress={go("/business/settings/start-screen")}
          />
          <SwitchCard
            icon={(c) => <ShieldQuestion size={20} color={c} />}
            label="Confirm before deleting"
            description="Ask before removing customers, orders or entries."
            value={settings.confirmBeforeDeleting}
            onValueChange={(confirmBeforeDeleting) => updateSettings({ confirmBeforeDeleting })}
          />
          <Card icon={(c) => <RefreshCw size={20} color={c} />} label="Stock order preferences" onPress={go("/business/settings/order-preferences")} />
        </CardSection>

        <CardSection title="Data & connectivity">
          <Card icon={(c) => <RefreshCw size={20} color={c} />} label="Sync" onPress={go("/business/settings/sync")} />
          <Card icon={(c) => <Smartphone size={20} color={c} />} label="Mobile data usage" onPress={go("/business/settings/mobile-data")} />
          <Card icon={(c) => <WifiOff size={20} color={c} />} label="Offline mode" onPress={go("/business/settings/offline-mode")} />
          <Card icon={(c) => <Database size={20} color={c} />} label="Storage & cache" onPress={go("/business/settings/storage")} />
        </CardSection>

        <CardSection title="Privacy">
          <Card icon={(c) => <Eye size={20} color={c} />} label="Business visibility" onPress={go("/business/settings/business-visibility")} />
          <Card icon={(c) => <Users size={20} color={c} />} label="Community activity" onPress={go("/business/settings/privacy-community")} />
          <Card icon={(c) => <BarChart3 size={20} color={c} />} label="Data usage" onPress={go("/business/settings/data-usage")} />
          <Card icon={(c) => <Sparkles size={20} color={c} />} label="Personalisation" onPress={go("/business/settings/personalisation")} />
        </CardSection>

        <CardSection title="Support & information">
          <Card icon={(c) => <HelpCircle size={20} color={c} />} label="Help & support" onPress={go("/business/settings/help")} />
          <Card icon={(c) => <MessageSquareWarning size={20} color={c} />} label="Report a problem" onPress={go("/business/settings/report-problem")} />
          <Card icon={(c) => <ScrollText size={20} color={c} />} label="Privacy policy" onPress={go("/business/settings/privacy-policy")} />
          <Card icon={(c) => <FileText size={20} color={c} />} label="Terms of service" onPress={go("/business/settings/terms")} />
          <Card icon={(c) => <Info size={20} color={c} />} label="About TruConnect" onPress={go("/business/settings/about")} />
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

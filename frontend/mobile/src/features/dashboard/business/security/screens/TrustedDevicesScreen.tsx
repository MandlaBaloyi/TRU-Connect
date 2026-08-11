import React, { useCallback, useState } from "react";
import { ActivityIndicator, Alert, ScrollView, StyleSheet, View } from "react-native";
import { useFocusEffect } from "expo-router";
import { useTheme, Button } from "react-native-paper";
import { Smartphone } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { EmptyState } from "@/components/feedback/EmptyState";
import { SecurityHero, SecuritySection, SecurityListCard, SecurityNote, StatusPill, formatWhen } from "../components/SecurityUI";
import { getTrustedDevices, removeTrustedDevice } from "../services/securityService";
import type { TrustedDevice } from "../types";
import { spacing } from "@/theme/spacing";

/** Devices that skip 2FA on sign-in. Removing one is destructive, so
 *  it's always confirmed; the current device is never removable from
 *  here, which would be a confusing way to lock yourself out. */
export default function TrustedDevicesScreen() {
  const theme = useTheme();
  const [devices, setDevices] = useState<TrustedDevice[] | null>(null);

  useFocusEffect(
    useCallback(() => {
      let cancelled = false;
      getTrustedDevices().then((d) => {
        if (!cancelled) setDevices(d);
      });
      return () => {
        cancelled = true;
      };
    }, [])
  );

  const confirmRemove = (device: TrustedDevice) => {
    Alert.alert(
      `Remove ${device.name}?`,
      "This device will need to verify with two-factor authentication the next time it signs in.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Remove",
          style: "destructive",
          onPress: async () => {
            await removeTrustedDevice(device.id);
            setDevices(await getTrustedDevices());
          },
        },
      ]
    );
  };

  if (!devices) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <SecurityHero
          icon={<Smartphone size={28} color={theme.colors.primary} strokeWidth={1.8} />}
          title="Trusted devices"
          description="Devices you've marked as trusted skip the two-factor step when signing in."
        />

        {devices.length === 0 ? (
          <EmptyState
            icon={<Smartphone size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />}
            message="No trusted devices yet. Devices you choose to trust when signing in will show up here."
          />
        ) : (
          <>
            <SecuritySection>
              {devices.map((device) => (
                <SecurityListCard
                  key={device.id}
                  title={device.name}
                  subtitle={device.location}
                  meta={`Last used ${formatWhen(device.lastActiveAt)}`}
                  badge={device.isCurrentDevice ? <StatusPill label="This device" tone="on" /> : undefined}
                  action={
                    device.isCurrentDevice ? undefined : (
                      <Button mode="text" compact onPress={() => confirmRemove(device)} textColor={theme.colors.error}>
                        Remove
                      </Button>
                    )
                  }
                />
              ))}
            </SecuritySection>

            <SecurityNote>
              Only trust devices that belong to you — if you see something here you don't recognise, remove it and
              change your password.
            </SecurityNote>
          </>
        )}
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.lg },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
});

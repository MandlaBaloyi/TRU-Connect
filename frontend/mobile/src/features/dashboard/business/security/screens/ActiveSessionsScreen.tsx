import React, { useCallback, useState } from "react";
import { ActivityIndicator, Alert, ScrollView, StyleSheet, View } from "react-native";
import { useFocusEffect } from "expo-router";
import { useTheme, Button } from "react-native-paper";
import { MonitorSmartphone } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { SecondaryButton } from "@/components/ui/SecondaryButton";
import { SecurityHero, SecuritySection, SecurityListCard, SecurityNote, StatusPill, formatWhen } from "../components/SecurityUI";
import { getActiveSessions, endSession, endAllOtherSessions } from "../services/securityService";
import type { ActiveSession } from "../types";
import { spacing } from "@/theme/spacing";

/** Where the account is currently signed in. The current session is
 *  never endable from here — that's what Sign out is for. */
export default function ActiveSessionsScreen() {
  const theme = useTheme();
  const [sessions, setSessions] = useState<ActiveSession[] | null>(null);

  const refresh = async () => setSessions(await getActiveSessions());

  useFocusEffect(
    useCallback(() => {
      let cancelled = false;
      getActiveSessions().then((s) => {
        if (!cancelled) setSessions(s);
      });
      return () => {
        cancelled = true;
      };
    }, [])
  );

  const confirmEnd = (session: ActiveSession) => {
    Alert.alert(`Sign out ${session.deviceName}?`, "That device will need to sign in again.", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Sign out",
        style: "destructive",
        onPress: async () => {
          await endSession(session.id);
          await refresh();
        },
      },
    ]);
  };

  const confirmEndAll = () => {
    Alert.alert(
      "Sign out everywhere else?",
      "Every device except this one will be signed out. You'll stay signed in here.",
      [
        { text: "Cancel", style: "cancel" },
        {
          text: "Sign out others",
          style: "destructive",
          onPress: async () => {
            await endAllOtherSessions();
            await refresh();
          },
        },
      ]
    );
  };

  if (!sessions) {
    return (
      <ScreenContainer hasNativeHeader>
        <View style={styles.centre}>
          <ActivityIndicator color={theme.colors.primary} />
        </View>
      </ScreenContainer>
    );
  }

  const hasOthers = sessions.some((s) => !s.isCurrentSession);

  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <SecurityHero
          icon={<MonitorSmartphone size={28} color={theme.colors.primary} strokeWidth={1.8} />}
          title="Where you're signed in"
          description="Every device currently signed in to your account, in one place."
        />

        <SecuritySection>
          {sessions.map((session) => (
            <SecurityListCard
              key={session.id}
              title={session.deviceName}
              subtitle={session.location}
              meta={`Active ${formatWhen(session.lastActiveAt)}`}
              badge={session.isCurrentSession ? <StatusPill label="This device" tone="on" /> : undefined}
              action={
                session.isCurrentSession ? undefined : (
                  <Button mode="text" compact onPress={() => confirmEnd(session)} textColor={theme.colors.error}>
                    Sign out
                  </Button>
                )
              }
            />
          ))}
        </SecuritySection>

        {hasOthers && <SecondaryButton onPress={confirmEndAll}>Sign out everywhere else</SecondaryButton>}

        <SecurityNote>
          If you see a device here you don't recognise, sign it out and change your password straight away.
        </SecurityNote>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.lg },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
});

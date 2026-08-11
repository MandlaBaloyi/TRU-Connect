import React, { useEffect, useState } from "react";
import { ActivityIndicator, ScrollView, StyleSheet, View } from "react-native";
import { useTheme } from "react-native-paper";
import { History } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { EmptyState } from "@/components/feedback/EmptyState";
import { SecurityHero, SecuritySection, SecurityListCard, SecurityNote, StatusPill, formatWhen } from "../components/SecurityUI";
import { getLoginActivity } from "../services/securityService";
import type { LoginActivityEntry } from "../types";
import { spacing } from "@/theme/spacing";

/** Read-only history of sign-in attempts, successful and failed.
 *  Failed attempts are shown deliberately — they're how you notice
 *  someone is trying to get in. */
export default function LoginActivityScreen() {
  const theme = useTheme();
  const [entries, setEntries] = useState<LoginActivityEntry[] | null>(null);

  useEffect(() => {
    let cancelled = false;
    getLoginActivity().then((e) => {
      if (!cancelled) setEntries(e);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  if (!entries) {
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
          icon={<History size={28} color={theme.colors.primary} strokeWidth={1.8} />}
          title="Login activity"
          description="A record of recent sign-ins to your account, successful and failed."
        />

        {entries.length === 0 ? (
          <EmptyState
            icon={<History size={40} color={theme.colors.onSurfaceVariant} strokeWidth={1.5} />}
            message="No sign-in activity recorded yet."
          />
        ) : (
          <>
            <SecuritySection>
              {entries.map((entry) => (
                <SecurityListCard
                  key={entry.id}
                  title={entry.deviceName}
                  subtitle={entry.location}
                  meta={formatWhen(entry.occurredAt)}
                  badge={
                    entry.result === "FAILED" ? (
                      <StatusPill label="Failed" tone="warning" />
                    ) : (
                      <StatusPill label="Successful" tone="on" />
                    )
                  }
                />
              ))}
            </SecuritySection>

            <SecurityNote>
              A failed attempt on its own isn't unusual — a mistyped password looks the same as someone guessing. But
              several failed attempts from somewhere you don't recognise is worth acting on: change your password and
              turn on two-factor authentication.
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

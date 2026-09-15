import React, { useEffect } from "react";
import { View, ActivityIndicator, StyleSheet } from "react-native";
import { useTheme } from "react-native-paper";
import { useRouter } from "expo-router";
import { getEffectiveRole, isAuthenticated } from "@/navigation/routeGuards";
import { getSetupState } from "@/features/onboarding/business-setup/api/businessSetupApi";
import { hasSkippedLocation } from "@/features/onboarding/business-setup/hooks/useBusinessSetup";
import { SETUP_ROUTES } from "@/features/onboarding/business-setup/types";

/**
 * Role-aware dashboard entry point.
 *
 * Reads the authenticated user's role and forwards to the correct
 * dashboard, so sign-in / registration can always redirect to the single
 * stable target "/(dashboard)" without knowing the role.
 *
 * IMPORTANT: this file previously contained a duplicate of the SPLASH
 * screen, which redirected back to /(onboarding)/welcome. Since sign-in
 * redirects here, that produced an infinite loop and the dashboard was
 * unreachable. Do not paste splash-screen content into this file.
 *
 * ── THE SETUP GATE ────────────────────────────────────────────────
 *
 * IT LIVES HERE BECAUSE THIS IS ALREADY THE ONE FORK. Every
 * authenticated path in the app passes through this file, and it is
 * the only place that knows the role before a dashboard is chosen.
 * Putting the gate anywhere else means putting it in several places,
 * and the one that gets missed is the one somebody uses.
 *
 * IT FAILS OPEN, ALWAYS. If setup-state cannot be fetched -- no
 * network, a backend that is down, an older build talking to a newer
 * server -- the person goes to their dashboard. A gate that fails
 * CLOSED would lock an established shop out of an app that works
 * perfectly well without three answers it gave months ago, and it
 * would do it on exactly the day the network was bad.
 *
 * IT IS NEW-ACCOUNTS-ONLY IN EFFECT, NOT BY A FLAG. requiredComplete
 * is already true for anyone who has filled their trading details, so
 * existing shops never see it; the ones who have not are caught more
 * gently by the feed's own "tell us what you buy" rail, which asks
 * inside the screen its answer improves.
 */
export default function DashboardIndex() {
  const router = useRouter();
  const theme = useTheme();

  useEffect(() => {
    (async () => {
      if (!(await isAuthenticated())) {
        router.replace("/(auth)/sign-in");
        return;
      }

      const role = await getEffectiveRole();
      if (role === "supplier") {
        router.replace("/(dashboard)/supplier/home");
        return;
      }

      const next = await businessEntryRoute();
      router.replace(next as never);
    })();
  }, [router]);

  return (
    <View style={[styles.container, { backgroundColor: theme.colors.background }]}>
      <ActivityIndicator size="large" color={theme.colors.primary} />
    </View>
  );
}

/**
 * Where a business actually lands: their home, or the first setup step
 * they still owe.
 *
 * THE SKIP IS CHECKED ON THE CLIENT because that is where it is
 * recorded -- the server knows only whether a location exists, and
 * "they said not now" is a fact about this phone. Steps one and two
 * have no skip and are read straight off requiredComplete.
 */
async function businessEntryRoute(): Promise<string> {
  const home = "/(dashboard)/business/home";

  try {
    const setup = await getSetupState();

    if (!setup.requiredComplete && setup.nextStep) {
      return SETUP_ROUTES[setup.nextStep];
    }

    // The two required steps are done. The third is offered once, and
    // only if it has not already been declined on this device.
    if (!setup.steps.whereYouAre && !(await hasSkippedLocation())) {
      return SETUP_ROUTES.whereYouAre;
    }

    return home;
  } catch {
    return home;
  }
}

const styles = StyleSheet.create({
  container: { flex: 1, alignItems: "center", justifyContent: "center" },
});

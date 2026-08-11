import React from "react";
import { StyleSheet, View, Image } from "react-native";
import { Text, Divider } from "react-native-paper";
import { useRouter } from "expo-router";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { SecondaryButton } from "@/components/ui/SecondaryButton";
import { PolicyLinksText } from "@/components/legal/PolicyLinksText";
import { spacing } from "@/theme/spacing";

/**
 * Welcome Screen.
 * Logo only -- no repeated "TruConnect" wordmark, since the logo
 * artwork already carries the name. "Build Trust. Unlock Opportunity."
 * now carries the full weight of the supporting copy. Terms/Privacy
 * notice sits at the very bottom, below "I already have an account",
 * separated by a divider.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 2).
 */
export default function WelcomeScreen() {
  const router = useRouter();

  return (
    <ScreenContainer>
      <View style={styles.logoWrap}>
        <Image
          source={require("../../assets/images/tru-connect-logo.png")}
          style={styles.logo}
          resizeMode="contain"
        />

        <Text style={styles.tagline}>
          Build Trust.
          {"\n"}
          Unlock Opportunity.
        </Text>
      </View>

      <View style={styles.actions}>
        <PrimaryButton onPress={() => router.push("/(onboarding)/role-selection")}>
          Get Started
        </PrimaryButton>

        <SecondaryButton
          onPress={() => router.push("/(auth)/sign-in")}
          style={{ marginTop: spacing.sm }}
        >
          I already have an account
        </SecondaryButton>

        <Divider style={styles.divider} />

        <PolicyLinksText lead="By continuing, you agree to TruConnect's" style={styles.privacyNotice} />

        <Text variant="labelSmall" style={styles.poweredBy}>
          Powered by <Text style={styles.truePoint}>TruePoint</Text>
        </Text>
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  logoWrap: {
    flex: 1,
    alignItems: "center",
    justifyContent: "center",
  },

  logo: {
    width: 110,
    height: 110,
    marginBottom: spacing.lg,
    borderRadius: 20,
    backgroundColor: "#FFFFFF",
    shadowColor: "#0B2E59",
    shadowOffset: {
      width: 0,
      height: 8,
    },
    shadowOpacity: 0.08,
    shadowRadius: 18,
    elevation: 4,
  },

tagline: {
  marginTop: spacing.md,
  textAlign: "center",
  fontSize: 22,
  fontWeight: "700",
  fontStyle: "italic",
  lineHeight: 30,
  letterSpacing: 0.4,
  color: "#17335C", 
},

  actions: {
    marginBottom: spacing.lg,
  },

  divider: {
    marginTop: spacing.md,
    marginBottom: spacing.sm,
  },

  privacyNotice: {
    textAlign: "center",
    opacity: 0.65,
    lineHeight: 20,
  },

  poweredBy: {
    marginTop: spacing.md,
    textAlign: "center",
    opacity: 0.55,
    letterSpacing: 0.8,
    fontSize: 11,
  },

  truePoint: {
    fontWeight: "700",
    color: "#0B2E59",
  },
});
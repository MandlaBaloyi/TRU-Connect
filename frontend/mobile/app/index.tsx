import React, { useEffect } from "react";
import { StyleSheet, Image, View } from "react-native";
import { useTheme } from "react-native-paper";
import { useRouter } from "expo-router";

/**
 * Splash Screen.
 * Logo + wordmark on a theme-aware background (white in light mode,
 * dark in dark mode), sized and spaced to match the Welcome screen.
 *
 * No fade-in animation here on purpose: this is the very first thing a
 * user sees, and a broken/stuck animation (e.g. a Reanimated worklet
 * transform issue) can silently leave the whole screen blank with
 * nothing visibly wrong to debug. A static render is more reliable for
 * a screen this critical. Reintroduce a subtle animation later only
 * once Reanimated is confirmed stable end-to-end.
 *
 * SPLASH_DURATION_MS is set to 50 seconds for visual QA/testing.
 * Change it back to 5000 (5 seconds) before shipping.
 */
const SPLASH_DURATION_MS = 50000;

export default function SplashScreen() {
  const router = useRouter();
  const theme = useTheme();

  useEffect(() => {
    const timer = setTimeout(() => {
      router.replace("/(onboarding)/welcome");
    }, SPLASH_DURATION_MS);

    return () => clearTimeout(timer);
  }, [router]);

  return (
    <View
      style={[
        styles.container,
        { backgroundColor: theme.colors.background },
      ]}
    >
      <View style={styles.center}>
        <View style={styles.logoContainer}>
          <Image
            source={require("../assets/images/tru-connect-logo.png")}
            style={styles.logo}
            resizeMode="contain"
          />
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },

  center: {
    alignItems: "center",
    justifyContent: "center",
  },

  logoContainer: {
    width: 132,
    height: 132,

    borderRadius: 30,

    backgroundColor: "#FFFFFF",

    justifyContent: "center",
    alignItems: "center",

    shadowColor: "#0F2D52",
    shadowOffset: {
      width: 0,
      height: 10,
    },
    shadowOpacity: 0.08,
    shadowRadius: 18,

    elevation: 8,
  },

  logo: {
    width: 96,
    height: 96,
  },

  wordmark: {
    fontWeight: "700",
  },
});
import React, { useRef, useState } from "react";
import { StyleSheet, View, Pressable } from "react-native";
import { Text, useTheme } from "react-native-paper";
import { useRouter } from "expo-router";
import PagerView from "react-native-pager-view";
import {
  Store,
  Warehouse,
  Package,
  Receipt,
  ShieldCheck,
  ClipboardList,
  Users,
  TrendingUp,
  ChevronLeft,
  ChevronRight,
} from "lucide-react-native";
import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { PrimaryButton } from "@/components/ui/PrimaryButton";
import { FeatureTile } from "@/components/cards/FeatureTile";
import { spacing, radius } from "@/theme/spacing";
import { secureStorage } from "@/services/storage/secureStorage";
import { STORAGE_KEYS } from "@/constants/config";
import type { UserRole } from "@/features/auth/types";

interface RoleFeature {
  label: string;
  icon: (color: string) => React.ReactNode;
}

interface RoleSlide {
  role: UserRole;
  label: string;
  features: RoleFeature[];
}

const ROLE_SLIDES: RoleSlide[] = [
  {
    role: "business",
    label: "For Small Business",
    features: [
      { label: "Find Suppliers", icon: (c) => <Store size={22} color={c} /> },
      { label: "Place Orders", icon: (c) => <Package size={22} color={c} /> },
      { label: "Track Orders", icon: (c) => <Receipt size={22} color={c} /> },
      { label: "Get Verified", icon: (c) => <ShieldCheck size={22} color={c} /> },
    ],
  },
  {
    role: "supplier",
    label: "For Supplier Business",
    features: [
      { label: "List Products", icon: (c) => <Warehouse size={22} color={c} /> },
      { label: "Manage Orders", icon: (c) => <ClipboardList size={22} color={c} /> },
      { label: "Reach Businesses", icon: (c) => <Users size={22} color={c} /> },
      { label: "Grow Sales", icon: (c) => <TrendingUp size={22} color={c} /> },
    ],
  },
];

/**
 * Role Selection -- swipeable pager between "For Small Business" and
 * "For Supplier Business". Each slide previews that role's core
 * capabilities as an icon + label grid (reusing FeatureTile, the same
 * component the Home Dashboard uses for Quick Actions), rather than a
 * paragraph of description text.
 *
 * The centered slide IS the selection -- swiping chooses the role, there
 * is no separate tap-to-select step. Continue sits in a fixed footer
 * below the pager so it never moves while swiping.
 * Ref: docs/01_TRU_CONNECT_PRODUCT_SPECIFICATION.txt (Screen 3) and
 * docs/06_BUSINESS_RULES_AND_WORKFLOWS.txt, Sections 1-2.
 */
export default function RoleSelectionScreen() {
  const router = useRouter();
  const theme = useTheme();
  const pagerRef = useRef<PagerView>(null);
  const [activeIndex, setActiveIndex] = useState(0);

  const activeSlide = ROLE_SLIDES[activeIndex];

  const goToPage = (index: number) => {
    pagerRef.current?.setPage(index);
  };

  const handleContinue = async () => {
    await secureStorage.setItem(STORAGE_KEYS.SELECTED_ROLE, activeSlide.role);
    router.push("/(auth)/create-account");
  };

  return (
    <ScreenContainer>
      {/* Improved pill badge */}
      <View style={[styles.pill, { backgroundColor: theme.colors.primary }]}>
        <Text style={styles.pillText}>{activeSlide.label}</Text>
      </View>

      <View style={styles.pagerWrap}>
        {activeIndex > 0 && (
          <Pressable
            onPress={() => goToPage(activeIndex - 1)}
            style={[styles.arrow, styles.arrowLeft]}
            hitSlop={12}
          >
            <ChevronLeft size={18} color={theme.colors.onSurface} />
          </Pressable>
        )}
        {activeIndex < ROLE_SLIDES.length - 1 && (
          <Pressable
            onPress={() => goToPage(activeIndex + 1)}
            style={[styles.arrow, styles.arrowRight]}
            hitSlop={12}
          >
            <ChevronRight size={18} color={theme.colors.onSurface} />
          </Pressable>
        )}

        <PagerView
          ref={pagerRef}
          style={styles.pager}
          initialPage={0}
          onPageSelected={(e) => setActiveIndex(e.nativeEvent.position)}
        >
          {ROLE_SLIDES.map((slide) => (
            <View key={slide.role} style={styles.slide}>
              <View style={styles.featureGrid}>
                <View style={styles.featureRow}>
                  <FeatureTile
                    label={slide.features[0].label}
                    icon={slide.features[0].icon(theme.colors.primary)}
                  />
                  <FeatureTile
                    label={slide.features[1].label}
                    icon={slide.features[1].icon(theme.colors.primary)}
                  />
                </View>
                <View style={styles.featureRow}>
                  <FeatureTile
                    label={slide.features[2].label}
                    icon={slide.features[2].icon(theme.colors.primary)}
                  />
                  <FeatureTile
                    label={slide.features[3].label}
                    icon={slide.features[3].icon(theme.colors.primary)}
                  />
                </View>
              </View>
            </View>
          ))}
        </PagerView>
      </View>

      <View style={styles.dotsRow}>
        {ROLE_SLIDES.map((_, i) => {
          const isActive = i === activeIndex;
          return (
            <Pressable key={i} onPress={() => goToPage(i)} hitSlop={8}>
              <View
                style={[
                  styles.dot,
                  isActive
                    ? { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary }
                    : { backgroundColor: "transparent", borderColor: theme.colors.outline },
                ]}
              />
            </Pressable>
          );
        })}
      </View>

      <View style={styles.footer}>
        <PrimaryButton onPress={handleContinue}>Continue</PrimaryButton>
      </View>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  pill: {
    alignSelf: "center",
    paddingHorizontal: 22,
    paddingVertical: 8,
    borderRadius: radius.pill,
    marginTop: spacing.lg,
    marginBottom: spacing.md,
  },
  pillText: {
    color: "#FFFFFF",
    fontWeight: "700",
    fontSize: 15,
    letterSpacing: 0.3,
  },
  pagerWrap: { flex: 1, justifyContent: "center" },
  pager: { height: 420 },
  slide: {
    flex: 1,
    alignItems: "center",
    justifyContent: "flex-start",
    paddingHorizontal: spacing.lg,
    paddingTop: spacing.xl,
  },
  featureGrid: { width: "100%", gap: spacing.sm },
  featureRow: { flexDirection: "row", gap: spacing.sm },
  arrow: {
    position: "absolute",
    top: "50%",
    marginTop: -14,      // half of 28
    zIndex: 10,
    width: 28,
    height: 28,
    borderRadius: 14,
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: "rgba(0,0,0,0.06)",
    opacity: 0.45,
  },
  arrowLeft: { left: spacing.xs },
  arrowRight: { right: spacing.xs },
  dotsRow: { flexDirection: "row", justifyContent: "center", gap: 8, marginBottom: spacing.lg },
  dot: { width: 10, height: 10, borderRadius: 5, borderWidth: 1.5 },
  footer: { marginBottom: spacing.lg },
});
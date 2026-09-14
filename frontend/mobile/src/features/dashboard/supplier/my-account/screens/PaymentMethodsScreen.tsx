import React, { useLayoutEffect, useState } from "react";
import { ActivityIndicator, Alert, Pressable, ScrollView, StyleSheet, View } from "react-native";
import { useNavigation, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Banknote, CreditCard, Landmark, Plus, Star, Trash2, Wallet } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { Card, CardSection, ListCard, StatusPill } from "@/components/lists/CardListUI";
import { SectionHeading } from "@/components/ui/SectionHeading";
import { InfoHint } from "@/components/ui/InfoHint";

import { PaymentMethodsMenu } from "../components/PaymentMethodsMenu";
import { spacing } from "@/theme/spacing";

import { usePaymentMethods } from "../hooks/usePaymentMethods";
import { useSupplierProfileField } from "../hooks/useSupplierProfileField";
import type { PaymentMethod } from "../types";

// CASH stays in the map even though cash rows are filtered out of
// the list: method.type is "CASH" | "EFT", so the lookup needs the
// key to typecheck. Unreachable, not unused.
const METHOD_ICON = { CASH: Wallet, EFT: Landmark } as const;

/**
 * The RECEIVING side — direct mirror of business/my-account's own
 * PaymentMethodsScreen.tsx (see types.ts's own note on why: same
 * Cash/EFT model, opposite direction of money movement). Card/gateway
 * is the same real future capability, shown the same honest way — a
 * navigable Coming Soon row, not a disabled control.
 */
export default function PaymentMethodsScreen() {
  const router = useRouter();
  const navigation = useNavigation();
  const theme = useTheme();
  const [aboutOpen, setAboutOpen] = useState(false);

  useLayoutEffect(() => {
    navigation.setOptions({ headerRight: () => <PaymentMethodsMenu onAbout={() => setAboutOpen(true)} /> });
  }, [navigation]);
  const { paymentMethods, isLoading, removePaymentMethod, setDefaultPaymentMethod } = usePaymentMethods();
  const { profile, saveField: saveProfileField } = useSupplierProfileField();

  /**
   * CHANGING A RAIL IS CONFIRMED, NEVER INSTANT. It changes who can buy
   * from this supplier at all, and turning direct payment ON is the
   * moment they take on the risk that TruConnect cannot see that money
   * -- so that sentence belongs in the confirmation they tap, not only
   * in a note further down the screen they may never read.
   */
  const confirmToggleDirect = () => {
    if (!profile) return;
    const on = profile.acceptsDirectPayment;

    // THE LAST RAIL CANNOT BE TURNED OFF. Checkout validates every
    // method against these flags, so a supplier with neither is not a
    // cash-only supplier -- they are a shopfront that looks open and
    // refuses every order at the final step. This used to be a standing
    // note on the screen; it belongs here, at the moment somebody tries.
    if (on && !profile.acceptsDigitalPayment) {
      Alert.alert(
        "This is your only way to be paid",
        "Businesses couldn't order from you at all with this off. Set up card and online payment first, then you can turn direct payment off.",
        [
          { text: "Cancel", style: "cancel" },
          {
            text: "Set up online",
            onPress: () => router.push("/supplier/my-account/card-payments" as any),
          },
        ],
      );
      return;
    }

    const apply = () => saveProfileField({ acceptsDirectPayment: !on }).catch(() => {});

    if (on) {
      Alert.alert(
        "Stop accepting direct payment?",
        "Businesses won't be able to pay you with cash, an EFT or a deposit. Only card and online payment will be offered to them.",
        [
          { text: "Cancel", style: "cancel" },
          { text: "Turn off", style: "destructive", onPress: apply },
        ],
      );
      return;
    }

    Alert.alert(
      "Accept direct payment?",
      "Businesses will be able to pay you with cash, an EFT or a deposit, arranged directly with you. TruConnect never sees that money move, so we can't confirm a payment was made or step in if something goes wrong.",
      [
        { text: "Cancel", style: "cancel" },
        { text: "Accept", onPress: apply },
      ],
    );
  };

  const confirmRemove = (method: PaymentMethod) => {
    Alert.alert("Remove payment method", `Remove ${method.displayLabel}?`, [
      { text: "Cancel", style: "cancel" },
      { text: "Remove", style: "destructive", onPress: () => removePaymentMethod(method.id).catch(() => {}) },
    ]);
  };

  if (isLoading) {
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
        {/* THE RAILS, ABOVE THE ACCOUNTS, because they decide whether
            those accounts are reachable at all. Checkout validates every
            payment method against these two flags.

            ONE ROW PER DESTINATION. An earlier version of this screen
            listed "Online payment" here AND "Card & gateway payments"
            below -- two rows, one screen, the same router push. It also
            subtitled Direct payment with "Cash, EFT or a deposit",
            which is just a description of the account rows underneath
            it. Both are gone.

            NO STANDING EXPLANATION ANYWHERE ON THIS SCREEN. It had
            three paragraphs of grey body text at one point -- what
            direct payment means, what happens with both rails off, how
            cash and EFT are recorded. All of it moved: what a thing
            MEANS is in the ⋮, and what a CHOICE costs you is in that
            choice's own confirmation dialog, where it cannot be
            scrolled past. The rows themselves only say what they are. */}
        {profile && (
          <>
            <SectionHeading title="How you get paid" />
            <CardSection>
              <ListCard
                icon={(c) => <Banknote size={20} color={c} />}
                title="Direct payment"
                badge={
                  <StatusPill
                    label={profile.acceptsDirectPayment ? "On" : "Off"}
                    tone={profile.acceptsDirectPayment ? "on" : "off"}
                  />
                }
                onPress={confirmToggleDirect}
              />
              {/* NOT A TOGGLE. You cannot accept card payments by
                  flipping a switch -- there is a provider to set up
                  first, and acceptsDigitalPayment should follow that
                  setup rather than stand on its own. So this row
                  navigates, exactly as the old "Card & gateway
                  payments" row did; it IS that row, moved. */}
              <Card
                icon={(c) => <CreditCard size={20} color={c} />}
                label="Card & online payment"
                status={
                  <StatusPill
                    label={profile.acceptsDigitalPayment ? "On" : "Coming soon"}
                    tone={profile.acceptsDigitalPayment ? "on" : "off"}
                  />
                }
                onPress={() => router.push("/supplier/my-account/card-payments" as any)}
              />
            </CardSection>

          </>
        )}

        <SectionHeading title="Your accounts" />
        <CardSection>
          {/* CASH IS NOT AN ACCOUNT. It was listed here as one, with a
              wallet icon and a Default pill, but there is nothing to
              hold, verify, mask or remove -- notes change hands. An
              account is a place money can be SENT: an EFT bank account,
              or card details once the gateway is live. Whether cash is
              accepted at all is the "Direct payment" rail above, which
              is where that question actually belongs. */
          paymentMethods
            .filter((method) => method.type !== "CASH")
            .map((method) => {
            const Icon = METHOD_ICON[method.type];
            return (
              <ListCard
                key={method.id}
                icon={(c) => <Icon size={20} color={c} />}
                title={method.displayLabel}
                subtitle={method.maskedReference}
                badge={
                  // NO "Default" PILL. With one usable account it label
                  // led nothing -- default among what? It returns when
                  // there is a real choice to be default AMONG.
                  method.status === "PENDING_VERIFICATION" ? (
                    <StatusPill label="Pending" tone="warning" />
                  ) : undefined
                }
                action={
                  <View style={styles.actions}>
                    {!method.isDefault && (
                      <Pressable
                        onPress={() => setDefaultPaymentMethod(method.id).catch(() => {})}
                        accessibilityRole="button"
                        accessibilityLabel={`Make ${method.displayLabel} default`}
                        hitSlop={8}
                      >
                        <Star size={18} color={theme.colors.onSurfaceVariant} />
                      </Pressable>
                    )}
                    {/* Cash used to be in this list and could not be
                        removed, so the button was guarded. It is
                        filtered out above now -- every row here is a
                        real, removable account. */}
                    {(
                      <Pressable
                        onPress={() => confirmRemove(method)}
                        accessibilityRole="button"
                        accessibilityLabel={`Remove ${method.displayLabel}`}
                        hitSlop={8}
                      >
                        <Trash2 size={18} color={theme.colors.error} />
                      </Pressable>
                    )}
                  </View>
                }
                />
              );
            })}
        </CardSection>

        <CardSection>
          {/* COMING SOON, AND DELIBERATELY NOT LINKED. The add-payment
              screen exists, but its fields are a guess at what a real
              EFT setup needs -- account number, branch code, holder
              name, verification -- and guessing wrong here means asking
              a supplier for the wrong things about their bank account.
              The screen stays in the tree; nothing points at it until
              the real requirements are known. */}
          <Card
            icon={(c) => <Plus size={20} color={c} />}
            label="Add EFT bank account"
            status={<StatusPill label="Coming soon" tone="off" />}
            // Disabled rather than silently inert: a row that looks
            // tappable and does nothing reads as a bug.
            disabled
            onPress={() => {}}
          />
        </CardSection>

      </ScrollView>

      {/* ONE explanation for the whole screen, opened from the ⋮.
          Controlled InfoHint rather than a hand-built modal, so it
          looks like every other explanation in the app. */}
      <InfoHint
        open={aboutOpen}
        onClose={() => setAboutOpen(false)}
        title="How payments work"
        body={[
          "Businesses can only pay you by a method you accept. The rest are hidden from them before they even build a basket.",
          "Direct payment is cash, an EFT or a deposit, arranged between you and the business. TruConnect never sees that money move, so we can't confirm a payment was made or step in if something goes wrong.",
          "Card and online payment goes through TruConnect's payment provider, so there's a record of what was paid and when.",
          "One of the two has to stay on. With neither, a business can't place an order with you at all.",
        ]}
      />
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  content: { paddingVertical: spacing.lg, paddingBottom: spacing.xxl, gap: spacing.xl },
  centre: { flex: 1, alignItems: "center", justifyContent: "center" },
  actions: { flexDirection: "row", gap: spacing.md, alignItems: "center" },
});

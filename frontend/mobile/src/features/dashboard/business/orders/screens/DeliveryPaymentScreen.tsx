import React, { useEffect, useLayoutEffect, useState } from "react";
import { Alert, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { useLocalSearchParams, useNavigation, useRouter } from "expo-router";
import { useTheme } from "react-native-paper";
import { Banknote, Check, CreditCard, MapPin, Receipt, Search } from "lucide-react-native";

import { ScreenContainer } from "@/components/ui/ScreenContainer";
import { EntityHeaderTitle } from "@/components/navigation/EntityHeaderTitle";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { formatDeliveryAddress } from "@/features/dashboard/shared/location-picker/formatDeliveryAddress";
import { MapPickerModal } from "@/features/dashboard/shared/location-picker/MapPickerModal";
import { SearchAddressModal } from "@/features/dashboard/shared/location-picker/SearchAddressModal";
import type { DeliveryLocation } from "@/features/dashboard/shared/location-picker/types";
import type { DeliveryType, PaymentMethod } from "../types";
import { useCart } from "../hooks/useCart";
import {
  PAYMENT_METHOD_DESCRIPTIONS,
  PAYMENT_METHOD_LABELS,
  SELECTABLE_PAYMENT_METHODS,
} from "@/features/dashboard/shared/payment/paymentMethods";
import { useSupplierIdentity } from "../hooks/useSupplierIdentity";
import { formatCents } from "../../../supplier/products/services/productMapper";

const DELIVERY_OPTIONS: { value: DeliveryType; label: string }[] = [
  { value: "DELIVER", label: "Deliver" },
  { value: "COLLECT", label: "Collect" },
];

// DERIVED FROM SELECTABLE_PAYMENT_METHODS, not listed again here. Cash
// and Proof of Payment were never two rails -- TruConnect observed
// neither, so a buyer who picked proof-of-payment and then handed over
// notes was indistinguishable from one who transferred. They are one
// thing, DIRECT, described honestly.
const PAYMENT_OPTIONS: { value: PaymentMethod; label: string; description: string; Icon: typeof Banknote }[] =
  SELECTABLE_PAYMENT_METHODS.map((value) => ({
    value,
    label: PAYMENT_METHOD_LABELS[value],
    description: PAYMENT_METHOD_DESCRIPTIONS[value],
    Icon: value === "PAYFAST" ? Receipt : Banknote,
  }));

/**
 * Step 1 of 3 -- a real, full screen, not a bottom sheet.
 *
 * DELIVER vs COLLECT get genuinely different address handling, not
 * the same text box with a different label. DELIVER now offers TWO
 * real, separate entry points -- "Search address" (SearchAddressModal)
 * and "Choose on map" (MapPickerModal) -- not a text box, since a
 * real, saved business address still doesn't exist on the backend
 * (useSavedDeliveryAddress, orphaned by this change, was the old
 * plug-in point for that and returns a plain string that no longer
 * matches this screen's structured shape -- revisit it once a real
 * saved-address feature exists and returns something richer). Collect
 * is different in kind, not just missing data -- checking
 * SupplierProfile directly confirmed there's no real collection
 * address field there at all, only a general suburb/city "location"
 * column explicitly documented as never meant to hold a full street
 * address. A business genuinely can't type (or pin) the supplier's
 * own address themselves, so Collect keeps its existing honest
 * placeholder -- untouched by this change, on purpose (the supplier's
 * own pin-drop is separate, not-yet-scoped work).
 *
 * A REAL THIRD PAYMENT OPTION sits here -- "Pay Online (Card / Instant
 * EFT)". Tapping it shows "Coming soon" and never actually selects
 * it -- the real backend already correctly rejects PAYFAST as
 * unavailable, so this is never even attempted.
 *
 * NO "Confirm Order" BUTTON HERE -- deliberately. This screen only
 * collects the delivery/payment choice; the real submission lives on
 * the Review Order screen next.
 */
export default function DeliveryPaymentScreen() {
  const { supplierId } = useLocalSearchParams<{ supplierId: string }>();
  const router = useRouter();
  const navigation = useNavigation();
  const theme = useTheme();

  const { cart } = useCart(supplierId ?? "");
  // Reads the supplier from the cart when there is one, and from
  // their profile when there is not -- an empty cart must not blank
  // the header. See useSupplierIdentity.
  const supplier = useSupplierIdentity(supplierId ?? "");
  const offersDelivery = cart?.supplierOffersDelivery ?? true;
  const minimumOrderCents = cart?.supplierMinimumOrderCents ?? null;
  const collectionAddress = cart?.supplierCollectionAddress ?? null;
  const supplierName = cart?.supplierName ?? "This supplier";
  const shortfallCents =
    minimumOrderCents !== null && cart ? Math.max(0, minimumOrderCents - cart.totalCents) : 0;
  const isBelowMinimum = shortfallCents > 0;

  /* THE SAME SOCIAL TOP BAR AS THE CART, carried through checkout.
     Every step of cart -> delivery & payment -> review is about one
     supplier, and the header is the only thing on these screens that
     says which one -- there is no other mention of them on this
     screen at all once you are past the cart. Dropping the avatar and
     name here left the middle of the flow anonymous, which is exactly
     when a business is entering an address and choosing how to pay.

     Reads from the cart, which is warm: it is the screen this one is
     pushed from. Falls back to the layout's plain title while the
     name is unknown -- same guard as everywhere else. */
  useLayoutEffect(() => {
    navigation.setOptions({
      ...(supplier.name
        ? {
            headerTitle: () => (
              <EntityHeaderTitle name={supplier.name!} subtitle="Delivery & payment" photoUrl={supplier.photoUrl} />
            ),
          }
        : {}),
    });
  }, [navigation, supplier.name, supplier.photoUrl]);

  // DEFAULTS TO THE OPTION THAT ACTUALLY EXISTS. A supplier who
  // doesn't deliver used to still get a screen defaulted to "Deliver",
  // so the business filled in a whole address before being rejected at
  // submit. Now the screen opens on Collect for them.
  const [deliveryType, setDeliveryType] = useState<DeliveryType>(offersDelivery ? "DELIVER" : "COLLECT");

  // The cart loads after first render, so the default above can be
  // computed from a stale `true`. Correct it once the real answer
  // arrives -- but only away from an impossible choice, never
  // overriding a deliberate one the business made themselves.
  useEffect(() => {
    if (!offersDelivery) setDeliveryType("COLLECT");
  }, [offersDelivery]);
  const [paymentMethod, setPaymentMethod] = useState<PaymentMethod | null>(null);
  const [deliveryLocation, setDeliveryLocation] = useState<DeliveryLocation | null>(null);
  const [isMapPickerVisible, setIsMapPickerVisible] = useState(false);
  const [isSearchModalVisible, setIsSearchModalVisible] = useState(false);
  // Set only when the business picked a search result -- opens the
  // map picker already centered there instead of resolving device
  // location. Cleared once the map picker closes, so "Choose location
  // on map" tapped directly afterward starts fresh, not still seeded
  // by a stale search.
  const [mapPresetCenter, setMapPresetCenter] = useState<{ latitude: number; longitude: number } | null>(null);

  const handleContinue = () => {
    if (!paymentMethod) return;
    // Both are enforced for real in checkout_service; these stop the
    // business walking two more screens to be told no.
    if (deliveryType === "DELIVER" && !offersDelivery) {
      Alert.alert("Collection only", `${supplierName} only accepts collection orders. Choose Collect to continue.`);
      return;
    }
    if (isBelowMinimum) {
      Alert.alert(
        "Order is below the minimum",
        `${supplierName} has a minimum order of ${formatCents(minimumOrderCents ?? 0)}. Add ${formatCents(
          shortfallCents
        )} more to your cart to continue.`
      );
      return;
    }
    if (deliveryType === "DELIVER" && !deliveryLocation) {
      Alert.alert("Address needed", "Choose your delivery location on the map to continue.");
      return;
    }
    router.push({
      pathname: `/business/orders/${supplierId}/review` as any,
      params: {
        paymentMethod,
        deliveryType,
        deliveryAddressText:
          deliveryType === "DELIVER" && deliveryLocation
            ? formatDeliveryAddress(deliveryLocation)
            : "Provided by the supplier upon collection",
        // Structured fields + coordinates -- COLLECT never sends any
        // of these (the backend ignores them for COLLECT regardless,
        // but there's genuinely nothing to send here either way).
        ...(deliveryType === "DELIVER" && deliveryLocation
          ? {
              deliveryBuilding: deliveryLocation.building,
              deliveryStreet: deliveryLocation.street,
              deliverySuburb: deliveryLocation.suburb,
              deliveryCity: deliveryLocation.city,
              deliveryProvince: deliveryLocation.province,
              deliveryPostalCode: deliveryLocation.postalCode,
              deliveryLatitude: String(deliveryLocation.latitude),
              deliveryLongitude: String(deliveryLocation.longitude),
            }
          : {}),
      },
    });
  };

  const handlePayOnline = () => {
    Alert.alert("Coming soon", "Paying online isn't available yet, but it's on the way.");
  };


  return (
    <ScreenContainer hasNativeHeader>
      <ScrollView contentContainerStyle={styles.content}>
        {/* THE MINIMUM, STATED UP FRONT. Finding out only on Continue
            means filling in an address and picking a payment method
            first -- this says it before any of that, and names the
            exact shortfall so the business doesn't do the arithmetic. */}
        {isBelowMinimum && (
          <View style={[styles.minimumBanner, { backgroundColor: theme.colors.errorContainer }]}>
            <Text style={[styles.minimumBannerText, { color: theme.colors.error }]}>
              {supplierName} has a minimum order of {formatCents(minimumOrderCents ?? 0)}. Add{" "}
              {formatCents(shortfallCents)} more to your cart to place this order.
            </Text>
          </View>
        )}

        <Text style={[styles.sectionTitle, { color: theme.colors.onSurface }]}>Deliver or collect?</Text>
        <View style={styles.segmentRow}>
          {DELIVERY_OPTIONS.map((option) => {
            const isSelected = option.value === deliveryType;
            return (
              <Pressable
                key={option.value}
                onPress={() => setDeliveryType(option.value)}
                style={[
                  styles.segment,
                  { borderColor: theme.colors.outline },
                  isSelected && { backgroundColor: theme.colors.primary, borderColor: theme.colors.primary },
                ]}
                accessibilityRole="button"
                accessibilityState={{ selected: isSelected }}
              >
                <Text style={[styles.segmentLabel, { color: isSelected ? theme.colors.onPrimary : theme.colors.onSurface }]}>
                  {option.label}
                </Text>
              </Pressable>
            );
          })}
        </View>

        <Text style={[styles.sectionTitle, styles.sectionSpacing, { color: theme.colors.onSurface }]}>
          {deliveryType === "COLLECT" ? "Collection address" : "Delivery address"}
        </Text>
        {deliveryType === "DELIVER" && !offersDelivery ? (
          // NO SEARCH, NO MAP -- just the supplier's own answer. Showing
          // address pickers here would invite a business to fill in a
          // delivery address for an order that can never be delivered.
          <View style={[styles.collectNotice, { borderColor: theme.colors.error, backgroundColor: theme.colors.errorContainer }]}>
            <MapPin size={18} color={theme.colors.error} strokeWidth={2} />
            <Text style={[styles.collectNoticeText, { color: theme.colors.error }]}>
              {supplierName} only accepts collection orders. Choose Collect above to continue.
            </Text>
          </View>
        ) : deliveryType === "DELIVER" ? (
          deliveryLocation ? (
            <Pressable
              onPress={() => setIsMapPickerVisible(true)}
              style={[styles.confirmedAddress, { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface }]}
              accessibilityRole="button"
              accessibilityLabel="Edit delivery address"
            >
              <MapPin size={18} color={theme.colors.primary} strokeWidth={2} />
              <Text style={[styles.confirmedAddressText, { color: theme.colors.onSurface }]}>
                {formatDeliveryAddress(deliveryLocation)}
              </Text>
              <Text style={[styles.editLabel, { color: theme.colors.primary }]}>Edit</Text>
            </Pressable>
          ) : (
            <View style={styles.locationOptionsRow}>
              <Pressable
                onPress={() => setIsSearchModalVisible(true)}
                style={[styles.chooseLocationButton, styles.locationOptionHalf, { borderColor: theme.colors.outline }]}
                accessibilityRole="button"
                accessibilityLabel="Search your address"
              >
                <Search size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
                <Text style={[styles.chooseLocationText, { color: theme.colors.onSurface }]}>Search address</Text>
              </Pressable>
              <Pressable
                onPress={() => {
                  setMapPresetCenter(null);
                  setIsMapPickerVisible(true);
                }}
                style={[styles.chooseLocationButton, styles.locationOptionHalf, { borderColor: theme.colors.outline }]}
                accessibilityRole="button"
                accessibilityLabel="Choose location on map"
              >
                <MapPin size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
                <Text style={[styles.chooseLocationText, { color: theme.colors.onSurface }]}>Choose on map</Text>
              </Pressable>
            </View>
          )
        ) : (
          <View style={[styles.collectNotice, { borderColor: theme.colors.outline, backgroundColor: theme.colors.surfaceVariant }]}>
            <MapPin size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
            <Text style={[styles.collectNoticeText, { color: theme.colors.onSurfaceVariant }]}>
              {/* Real now -- suppliers can finally set this (My Account ->
                  Profile -> Collection address). The old copy was the
                  only thing this branch could say when nothing anywhere
                  let them enter one. */}
              {collectionAddress
                ? [
                    collectionAddress.building,
                    collectionAddress.street,
                    collectionAddress.suburb,
                    [collectionAddress.city, collectionAddress.province].filter(Boolean).join(", "),
                    collectionAddress.postalCode,
                  ]
                    .filter((part) => Boolean(part && part.trim()))
                    .join(", ")
                : `${supplierName} hasn't added a collection address yet — they'll confirm where to collect when they accept your order.`}
            </Text>
          </View>
        )}

        <SearchAddressModal
          visible={isSearchModalVisible}
          onClose={() => setIsSearchModalVisible(false)}
          onLocationFound={(location) => {
            setMapPresetCenter(location);
            setIsMapPickerVisible(true);
          }}
        />

        <MapPickerModal
          visible={isMapPickerVisible}
          presetCenter={mapPresetCenter}
          onClose={() => {
            setIsMapPickerVisible(false);
            setMapPresetCenter(null);
          }}
          onConfirm={(location) => {
            setDeliveryLocation(location);
            setMapPresetCenter(null);
          }}
        />

        <Text style={[styles.sectionTitle, styles.sectionSpacing, { color: theme.colors.onSurface }]}>How will you pay?</Text>
        {PAYMENT_OPTIONS.map((option) => {
          const isSelected = option.value === paymentMethod;
          return (
            <Pressable
              key={option.value}
              onPress={() => setPaymentMethod(option.value)}
              style={[
                styles.optionRow,
                { borderColor: theme.colors.outline },
                isSelected && { borderColor: theme.colors.primary, backgroundColor: theme.colors.primaryContainer },
              ]}
              accessibilityRole="radio"
              accessibilityState={{ checked: isSelected }}
            >
              <option.Icon size={22} color={isSelected ? theme.colors.primary : theme.colors.onSurfaceVariant} strokeWidth={2} />
              <View style={styles.rowText}>
                <Text style={[styles.rowLabel, { color: theme.colors.onSurface }]}>{option.label}</Text>
                <Text style={[styles.rowDescription, { color: theme.colors.onSurfaceVariant }]}>{option.description}</Text>
              </View>
              {isSelected && <Check size={18} color={theme.colors.primary} strokeWidth={2.5} />}
            </Pressable>
          );
        })}

        <Pressable
          onPress={handlePayOnline}
          style={[styles.optionRow, { borderColor: theme.colors.outline }]}
          accessibilityRole="button"
          accessibilityLabel="Pay Online"
        >
          <CreditCard size={22} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
          <View style={styles.rowText}>
            <Text style={[styles.rowLabel, { color: theme.colors.onSurface }]}>Pay Online (Card / Instant EFT)</Text>
            <Text style={[styles.rowDescription, { color: theme.colors.onSurfaceVariant }]}>Coming soon</Text>
          </View>
        </Pressable>

        <Pressable
          onPress={handleContinue}
          disabled={!paymentMethod}
          style={[styles.continueButton, { backgroundColor: theme.colors.primary }, !paymentMethod && styles.continueButtonDisabled]}
          accessibilityRole="button"
          accessibilityLabel="Continue to review"
        >
          <Text style={[styles.continueLabel, { color: theme.colors.onPrimary }]}>Continue to Review</Text>
        </Pressable>
      </ScrollView>
    </ScreenContainer>
  );
}

const styles = StyleSheet.create({
  minimumBanner: { borderRadius: radius.lg, padding: spacing.md, marginBottom: spacing.md },
  minimumBannerText: { ...typography.bodySmall, fontWeight: "600", lineHeight: 19 },
  content: { padding: spacing.md, paddingBottom: spacing.xl },
  sectionTitle: { ...typography.h2, fontWeight: "700", marginBottom: spacing.sm },
  sectionSpacing: { marginTop: spacing.lg },
  segmentRow: { flexDirection: "row", gap: spacing.sm },
  segment: { flex: 1, minHeight: 44, borderWidth: 1, borderRadius: radius.md, alignItems: "center", justifyContent: "center" },
  segmentLabel: { ...typography.body, fontWeight: "700" },
  locationOptionsRow: { flexDirection: "row", gap: spacing.sm },
  locationOptionHalf: { flex: 1, justifyContent: "center" },
  chooseLocationButton: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.xs,
    minHeight: 48,
    borderWidth: 1,
    borderStyle: "dashed",
    borderRadius: radius.md,
    paddingHorizontal: spacing.sm,
  },
  chooseLocationText: { ...typography.body, fontWeight: "700" },
  confirmedAddress: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    minHeight: 48,
    borderWidth: 1,
    borderRadius: radius.md,
    paddingHorizontal: spacing.sm,
  },
  confirmedAddressText: { ...typography.body, flex: 1 },
  editLabel: { ...typography.bodySmall, fontWeight: "700" },
  collectNotice: { flexDirection: "row", alignItems: "flex-start", gap: spacing.sm, borderWidth: 1, borderRadius: radius.md, padding: spacing.sm },
  collectNoticeText: { ...typography.bodySmall, flex: 1 },
  optionRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: spacing.sm,
    minHeight: 56,
    borderWidth: 1,
    borderRadius: radius.md,
    paddingHorizontal: spacing.sm,
    marginBottom: spacing.sm,
  },
  rowText: { flex: 1, paddingRight: spacing.sm },
  rowLabel: { ...typography.body, fontWeight: "700" },
  rowDescription: { ...typography.bodySmall },
  continueButton: { marginTop: spacing.lg, minHeight: 48, borderRadius: radius.md, alignItems: "center", justifyContent: "center" },
  continueButtonDisabled: { opacity: 0.5 },
  continueLabel: { fontWeight: "700", fontSize: 15 },
});

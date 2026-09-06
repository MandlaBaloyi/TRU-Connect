import React, { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { MapPin, Search } from "lucide-react-native";

import { MapPickerModal } from "@/features/dashboard/shared/location-picker/MapPickerModal";
import { SearchAddressModal } from "@/features/dashboard/shared/location-picker/SearchAddressModal";
import type { DeliveryLocation } from "@/features/dashboard/shared/location-picker/types";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * Where the SUPPLIER sets their own collection address.
 *
 * THE MISSING HALF OF A FEATURE THAT WAS ALREADY HALF-BUILT: the
 * collection_* columns, the business-facing "Collect from" block, and
 * the checkout screen's COLLECT branch all existed, but nothing
 * anywhere let a supplier actually enter the address — so that branch
 * could only ever say "will appear here once they've added one". This
 * is the "once".
 *
 * DELIBERATELY THE SAME TWO ENTRY POINTS AS THE BUSINESS DELIVERY
 * FLOW (DeliveryPaymentScreen): "Search address" (SearchAddressModal,
 * Mapbox geocoding) then confirm on the map, or "Choose on map"
 * (MapPickerModal) directly. Reusing those exact components rather
 * than a second address UI means one set of address semantics, one
 * geocoder, one confirm gesture — and a supplier who is also a
 * business elsewhere in the app sees the flow they already know.
 *
 * SEARCH FEEDS THE MAP, IT DOESN'T SKIP IT. A geocoded result is a
 * best guess; the supplier still confirms the exact pin, because this
 * address is what a business will actually drive to.
 */
export function CollectionAddressField({
  value,
  onSave,
}: {
  value: DeliveryLocation | null;
  onSave: (location: DeliveryLocation) => Promise<void>;
}) {
  const theme = useTheme();
  const [isSearchVisible, setIsSearchVisible] = useState(false);
  const [isMapVisible, setIsMapVisible] = useState(false);
  // Set only when a search result was picked -- opens the map already
  // centred there rather than on device location. Cleared on close so
  // a later "Choose on map" starts fresh, not seeded by a stale search.
  const [presetCenter, setPresetCenter] = useState<{ latitude: number; longitude: number } | null>(null);

  const lines = value
    ? [
        value.building,
        value.street,
        value.suburb,
        [value.city, value.province].filter(Boolean).join(", "),
        value.postalCode,
      ].filter((part) => Boolean(part && part.trim()))
    : [];

  return (
    <View style={styles.wrap}>
      {lines.length > 0 ? (
        <Pressable
          onPress={() => {
            setPresetCenter(
              value ? { latitude: value.latitude, longitude: value.longitude } : null
            );
            setIsMapVisible(true);
          }}
          style={[styles.card, { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface }]}
          accessibilityRole="button"
          accessibilityLabel="Edit collection address"
        >
          <MapPin size={18} color={theme.colors.primary} strokeWidth={2} />
          <Text style={[styles.address, { color: theme.colors.onSurface }]}>{lines.join("\n")}</Text>
          <Text style={[styles.edit, { color: theme.colors.primary }]}>Edit</Text>
        </Pressable>
      ) : (
        <View style={styles.optionsRow}>
          <Pressable
            onPress={() => setIsSearchVisible(true)}
            style={[styles.option, { borderColor: theme.colors.outline }]}
            accessibilityRole="button"
            accessibilityLabel="Search your address"
          >
            <Search size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
            <Text style={[styles.optionText, { color: theme.colors.onSurface }]}>Search address</Text>
          </Pressable>
          <Pressable
            onPress={() => {
              setPresetCenter(null);
              setIsMapVisible(true);
            }}
            style={[styles.option, { borderColor: theme.colors.outline }]}
            accessibilityRole="button"
            accessibilityLabel="Choose location on map"
          >
            <MapPin size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
            <Text style={[styles.optionText, { color: theme.colors.onSurface }]}>Choose on map</Text>
          </Pressable>
        </View>
      )}

      <SearchAddressModal
        visible={isSearchVisible}
        onClose={() => setIsSearchVisible(false)}
        onLocationFound={(location) => {
          setPresetCenter(location);
          setIsMapVisible(true);
        }}
      />

      <MapPickerModal
        visible={isMapVisible}
        presetCenter={presetCenter}
        onClose={() => {
          setIsMapVisible(false);
          setPresetCenter(null);
        }}
        onConfirm={(location) => {
          setPresetCenter(null);
          void onSave(location);
        }}
      />
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { gap: spacing.sm },
  card: {
    flexDirection: "row",
    alignItems: "flex-start",
    gap: spacing.md,
    padding: spacing.md,
    borderRadius: radius.lg,
    borderWidth: 1,
  },
  address: { ...typography.bodySmall, flex: 1, lineHeight: 19 },
  edit: { ...typography.bodySmall, fontWeight: "700" },
  optionsRow: { flexDirection: "row", gap: spacing.sm },
  option: {
    flex: 1,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: spacing.xs,
    paddingVertical: spacing.md,
    borderRadius: radius.lg,
    borderWidth: 1,
  },
  optionText: { ...typography.bodySmall, fontWeight: "700" },
});

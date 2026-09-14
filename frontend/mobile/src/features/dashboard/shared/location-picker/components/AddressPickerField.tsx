import React, { useState } from "react";
import { Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { MapPin, Search } from "lucide-react-native";

import { MapPickerModal } from "../MapPickerModal";
import { SearchAddressModal } from "../SearchAddressModal";
import type { DeliveryLocation } from "../types";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

/**
 * Set a place on the map: search for it, or drop the pin yourself.
 *
 * EXTRACTED FROM CollectionAddressField RATHER THAN COPIED, when the
 * business profile needed the same thing. That component's own
 * docstring already made the argument -- "reusing those exact
 * components rather than a second address UI means one set of address
 * semantics, one geocoder, one confirm gesture" -- and a second copy
 * would have been the first step in breaking it. Everything here was
 * already generic except two accessibility strings, which are props now.
 *
 * TWO ENTRY POINTS, AND SEARCH FEEDS THE MAP RATHER THAN SKIPPING IT.
 * A geocoded result is a best guess; the pin is confirmed by a person
 * either way, because in an informal settlement the difference between
 * the guess and the gate is the whole delivery.
 *
 * THE COORDINATES COME OFF THE MAP WIDGET, NEVER OFF THE GEOCODER, and
 * that is not only accuracy. Mapbox bills a stored geocode: every
 * request defaults to *temporary* (free, show-don't-store) unless
 * permanent=true, which needs a card on file and has no free allowance
 * at all. Reading the pin's own lat/lng keeps every call this app makes
 * inside the free tier by construction, not by policy. See the backend's
 * geocoding_config.py, which decided this.
 */
export function AddressPickerField({
  value,
  onSave,
  editLabel,
  searchLabel = "Search address",
  mapLabel = "Choose on map",
  searchA11yLabel,
  mapA11yLabel,
  pickerTitle,
  pickerConfirmLabel,
}: {
  value: DeliveryLocation | null;
  onSave: (location: DeliveryLocation) => void | Promise<void>;
  /** Spoken label for the filled-in card, e.g. "Edit collection address". */
  editLabel: string;
  searchLabel?: string;
  mapLabel?: string;
  /** Spoken labels, when they should differ from the visible text --
   *  the supplier field says "Search YOUR address" aloud while the
   *  button reads "Search address", and extracting this component
   *  should not quietly flatten that. */
  searchA11yLabel?: string;
  mapA11yLabel?: string;
  /** What the map screen calls this pin. Passed straight through --
   *  a supplier setting a collection address must not be asked to
   *  "confirm your delivery address". */
  pickerTitle?: string;
  pickerConfirmLabel?: string;
}) {
  const theme = useTheme();
  const [isSearchVisible, setIsSearchVisible] = useState(false);
  const [isMapVisible, setIsMapVisible] = useState(false);
  // Set only when a search result was picked -- opens the map already
  // centred there rather than on device location. Cleared on close so
  // a later "Choose on map" starts fresh, not seeded by a stale search.
  const [presetCenter, setPresetCenter] = useState<{ latitude: number; longitude: number } | null>(
    null
  );

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
            setPresetCenter(value ? { latitude: value.latitude, longitude: value.longitude } : null);
            setIsMapVisible(true);
          }}
          style={[
            styles.card,
            { borderColor: theme.colors.outline, backgroundColor: theme.colors.surface },
          ]}
          accessibilityRole="button"
          accessibilityLabel={editLabel}
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
            accessibilityLabel={searchA11yLabel ?? searchLabel}
          >
            <Search size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
            <Text style={[styles.optionText, { color: theme.colors.onSurface }]}>{searchLabel}</Text>
          </Pressable>
          <Pressable
            onPress={() => {
              setPresetCenter(null);
              setIsMapVisible(true);
            }}
            style={[styles.option, { borderColor: theme.colors.outline }]}
            accessibilityRole="button"
            accessibilityLabel={mapA11yLabel ?? mapLabel}
          >
            <MapPin size={18} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
            <Text style={[styles.optionText, { color: theme.colors.onSurface }]}>{mapLabel}</Text>
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
        title={pickerTitle}
        confirmLabel={pickerConfirmLabel}
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
    gap: spacing.sm,
    paddingVertical: spacing.md,
    borderRadius: radius.lg,
    borderWidth: 1,
  },
  optionText: { ...typography.bodySmall, fontWeight: "600" },
});

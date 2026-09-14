import React, { useState } from "react";
import { ActivityIndicator, Alert, Modal, Pressable, ScrollView, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useTheme } from "react-native-paper";
import { StatusBar } from "expo-status-bar";
import { X } from "lucide-react-native";
import * as Location from "expo-location";
import { WebView, WebViewMessageEvent } from "react-native-webview";

import { MAPBOX_PUBLIC_TOKEN } from "@/constants/config";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { AddressFieldsForm } from "./components/AddressFieldsForm";
import { useReverseGeocode } from "./hooks/useReverseGeocode";
import { buildMapPickerHtml } from "./mapPickerHtml";
import type { DeliveryLocation } from "./types";

interface Props {
  visible: boolean;
  onClose: () => void;
  onConfirm: (location: DeliveryLocation) => void;
  /** When given (a location picked via SearchAddressModal), the map
   *  opens centered there directly -- device-location resolution is
   *  skipped entirely, since a deliberate search result is a more
   *  precise starting point than a raw GPS fix anyway. Omit this
   *  entirely for the plain "choose location on map" entry point. */
  presetCenter?: { latitude: number; longitude: number } | null;
  /** What this pin IS. Defaults to the delivery wording this modal was
   *  written for, because that was its only caller for a while -- but
   *  it is now also used to set a SUPPLIER'S COLLECTION ADDRESS and a
   *  SHOP'S OWN LOCATION, and telling either of them to "confirm your
   *  delivery address" is simply wrong. Reusing a screen is right;
   *  reusing its sentences is not. */
  title?: string;
  confirmLabel?: string;
}

// The FALLBACK ONLY -- used when there's no presetCenter AND
// permission is denied, the device can't get a fix, or it takes too
// long. Roughly the middle of South Africa, so a business still
// starts on a real, on-country view rather than the ocean at [0, 0].
const DEFAULT_LATITUDE = -28.4793;
const DEFAULT_LONGITUDE = 24.6727;

// A hard ceiling on how long this screen waits for a GPS fix before
// giving up and falling back -- getCurrentPositionAsync has no
// built-in timeout in every SDK version, so this is enforced by hand
// with Promise.race. Opening the picker must never hang indefinitely
// on a weak signal; the business can always pan manually either way.
const LOCATION_TIMEOUT_MS = 8000;

const EMPTY_FIELDS = { building: "", street: "", suburb: "", city: "", province: "", postalCode: "" };

/** How the starting center was decided -- drives both the initial
 *  zoom level and the hint text under the map. Three genuinely
 *  different situations, not one boolean: a search result and a GPS
 *  fix are both "precise" (zoom in close), but only a failed/denied
 *  GPS fix needs the "couldn't use your location" explanation --
 *  a preset center from search never did any location lookup, there
 *  was nothing to fail. */
type StartMode = "preset" | "device" | "fallback";

async function resolveDeviceLocation(): Promise<{ latitude: number; longitude: number } | null> {
  const { status } = await Location.requestForegroundPermissionsAsync();
  if (status !== "granted") return null;

  const fix = await Promise.race([
    Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Balanced }),
    new Promise<null>((resolve) => setTimeout(() => resolve(null), LOCATION_TIMEOUT_MS)),
  ]);
  if (!fix) return null;

  return { latitude: fix.coords.latitude, longitude: fix.coords.longitude };
}

/**
 * MapPickerModal -- a real, full-screen React Native Modal (same
 * component NotificationDetailSheet already uses elsewhere in this
 * app), not a custom overlay. Inside it, a WebView renders actual
 * Mapbox GL JS -- see mapPickerHtml.ts's own docstring for why a
 * WebView instead of @rnmapbox/maps (keeps this app on Expo Go,
 * no EAS dev-client migration forced by this one feature).
 *
 * SEARCH LIVES ELSEWHERE NOW -- SearchAddressModal, a genuinely
 * separate screen, not layered on top of this one. Live testing
 * showed cramming a search bar + dropdown above the map made this
 * screen's UI feel broken (the dropdown overlapping/competing with
 * the map for the same cramped space). DeliveryPaymentScreen now
 * offers two real, separate entry points -- "Search your address" and
 * "Choose location on map" -- and a search result hands off to THIS
 * screen via presetCenter rather than the two being one screen.
 *
 * OPENS ON THE DEVICE'S REAL CURRENT LOCATION when no presetCenter is
 * given and permission is granted and a fix arrives in time -- fixes
 * what live testing surfaced: defaulting to the middle of South
 * Africa meant a business had to drag the map a huge real-world
 * distance to reach anywhere recognizable. Permission denial or a
 * slow/failed fix is NEVER fatal -- falls back to the generic South
 * Africa center rather than blocking the picker from opening at all.
 *
 * THE WEBVIEW ISN'T MOUNTED UNTIL THE STARTING CENTER IS RESOLVED
 * (preset, real fix, or fallback) -- deliberately, not a premature
 * optimisation. buildMapPickerHtml bakes the initial center directly
 * into the HTML string at creation time; mounting the WebView early
 * and re-centering it later would mean either reloading the whole
 * page (a visible flash) or reaching into the running map instance
 * from outside. Showing a brief "Finding your location" state and
 * mounting once, with the right center from the start, is simpler.
 *
 * THE PIN'S COORDINATES ARE MAP-INTERACTION DATA, NEVER A GEOCODING
 * RESULT -- center below comes from the WebView's own postMessage
 * (what the map widget is currently centered on) once it's running,
 * not from reverseGeocode's response, and not from presetCenter
 * either (that only seeds the STARTING point -- the business can
 * still nudge the pin from there, and whatever the map settles on is
 * what's actually used). reverseGeocode is only ever used to PRE-FILL
 * the editable text fields; what actually gets confirmed and sent to
 * onConfirm is the business's own (possibly edited) text plus those
 * map-sourced coordinates.
 *
 * SafeAreaView imported from react-native-safe-area-context, NOT
 * react-native's own -- the core one is iOS-only, a genuine no-op on
 * Android (confirmed after a real device report of this screen's
 * header overlapping the status bar on Android). The explicit
 * <StatusBar> override exists for the same root cause on the other
 * axis: a full-screen Modal renders as its own top-level window on
 * Android, which doesn't inherit the app-level StatusBar style set
 * in app/_layout.tsx.
 */
export function MapPickerModal({
  visible,
  onClose,
  onConfirm,
  presetCenter,
  title = "Delivery address",
  confirmLabel = "Confirm delivery address",
}: Props) {
  const theme = useTheme();
  const [startingCenter, setStartingCenter] = useState<{ latitude: number; longitude: number } | null>(null);
  const [isResolvingLocation, setIsResolvingLocation] = useState(true);
  const [startMode, setStartMode] = useState<StartMode>("fallback");
  const [center, setCenter] = useState<{ latitude: number; longitude: number } | null>(null);
  const [fields, setFields] = useState(EMPTY_FIELDS);
  // Once the business edits ANY field by hand, further reverse-geocode
  // results stop overwriting the form -- otherwise a small accidental
  // nudge of the map after a manual correction would silently discard
  // it. They can always pan again deliberately; nothing is lost, this
  // just stops auto-fill from fighting a deliberate edit.
  const [hasEditedFields, setHasEditedFields] = useState(false);

  const { address, isLoading, failed } = useReverseGeocode(center?.latitude ?? null, center?.longitude ?? null);

  React.useEffect(() => {
    if (!visible) return;
    let cancelled = false;

    (async () => {
      if (presetCenter) {
        setStartingCenter(presetCenter);
        setStartMode("preset");
        setIsResolvingLocation(false);
        return;
      }

      const device = await resolveDeviceLocation().catch(() => null);
      if (cancelled) return;
      if (device) {
        setStartingCenter(device);
        setStartMode("device");
      } else {
        setStartingCenter({ latitude: DEFAULT_LATITUDE, longitude: DEFAULT_LONGITUDE });
        setStartMode("fallback");
      }
      setIsResolvingLocation(false);
    })();

    return () => {
      cancelled = true;
    };
  }, [visible, presetCenter]);

  React.useEffect(() => {
    if (!address || hasEditedFields) return;
    setFields({
      building: "",
      street: address.street ?? "",
      suburb: address.suburb ?? "",
      city: address.city ?? "",
      province: address.province ?? "",
      postalCode: address.postalCode ?? "",
    });
  }, [address, hasEditedFields]);

  const handleMessage = (event: WebViewMessageEvent) => {
    try {
      const message = JSON.parse(event.nativeEvent.data);
      if (message.type === "center") {
        setCenter({ latitude: message.latitude, longitude: message.longitude });
      }
    } catch {
      // A malformed message from the page is never fatal -- the pin
      // simply doesn't update for that one event; nothing else in
      // this screen depends on it succeeding.
    }
  };

  const handleFieldChange = (field: keyof typeof EMPTY_FIELDS, value: string) => {
    setHasEditedFields(true);
    setFields((current) => ({ ...current, [field]: value }));
  };

  const handleClose = () => {
    // Reset so the NEXT time this modal opens (e.g. the business
    // taps "Edit" after already confirming once) it starts fresh --
    // including re-resolving location, in case they granted
    // permission in Settings since the last time this was open.
    setStartingCenter(null);
    setIsResolvingLocation(true);
    setStartMode("fallback");
    setCenter(null);
    setFields(EMPTY_FIELDS);
    setHasEditedFields(false);
    onClose();
  };

  const handleConfirm = () => {
    if (!center) {
      Alert.alert("Move the map", "Pan the map to your delivery location first.");
      return;
    }
    if (!fields.street.trim() && !fields.suburb.trim()) {
      Alert.alert("Address needed", "Add at least a street or suburb before confirming.");
      return;
    }
    onConfirm({ ...fields, latitude: center.latitude, longitude: center.longitude });
    handleClose();
  };

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={handleClose}>
      {visible && <StatusBar style={theme.dark ? "light" : "dark"} />}
      <SafeAreaView style={[styles.safeArea, { backgroundColor: theme.colors.background }]}>
        <View style={[styles.header, { borderBottomColor: theme.colors.outline }]}>
          <Text style={[styles.headerTitle, { color: theme.colors.onSurface }]}>{title}</Text>
          <Pressable onPress={handleClose} hitSlop={10} accessibilityRole="button" accessibilityLabel="Close">
            <X size={22} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
          </Pressable>
        </View>

        <View style={styles.mapWrap}>
          {isResolvingLocation || !startingCenter ? (
            <View style={[styles.mapLoading, { backgroundColor: theme.colors.surfaceVariant }]}>
              <ActivityIndicator color={theme.colors.primary} />
              <Text style={[styles.mapLoadingText, { color: theme.colors.onSurfaceVariant }]}>Finding your location...</Text>
            </View>
          ) : (
            <WebView
              originWhitelist={["*"]}
              source={{
                html: buildMapPickerHtml(
                  MAPBOX_PUBLIC_TOKEN,
                  startingCenter.latitude,
                  startingCenter.longitude,
                  // A search result or a real GPS fix can both start
                  // close in (street-level) -- only the country-wide
                  // fallback needs to start zoomed out enough to
                  // actually navigate from.
                  startMode === "fallback" ? 6 : 16
                ),
              }}
              onMessage={handleMessage}
              style={styles.map}
            />
          )}
        </View>
        <Text style={[styles.mapHint, { color: theme.colors.onSurfaceVariant }]}>
          {startMode === "fallback" && !isResolvingLocation
            ? "Couldn't use your location -- move the map to your delivery spot"
            : "Move the map to fine-tune your delivery location"}
        </Text>

        <ScrollView contentContainerStyle={styles.formContent}>
          <AddressFieldsForm values={fields} onChange={handleFieldChange} />
          {isLoading && (
            <Text style={[styles.statusText, { color: theme.colors.onSurfaceVariant }]}>Looking up this address...</Text>
          )}
          {failed && !isLoading && (
            <Text style={[styles.statusText, { color: theme.colors.onSurfaceVariant }]}>
              Couldn't look up this address automatically -- fill the fields in yourself.
            </Text>
          )}

          <Pressable
            onPress={handleConfirm}
            style={[styles.confirmButton, { backgroundColor: theme.colors.primary }]}
            accessibilityRole="button"
            accessibilityLabel={confirmLabel}
          >
            <Text style={[styles.confirmLabel, { color: theme.colors.onPrimary }]}>{confirmLabel}</Text>
          </Pressable>
        </ScrollView>
      </SafeAreaView>
    </Modal>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1 },
  header: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingHorizontal: spacing.md,
    paddingVertical: spacing.sm,
    borderBottomWidth: 1,
  },
  headerTitle: { ...typography.h2, fontWeight: "700" },
  mapWrap: { height: 260 },
  map: { flex: 1 },
  mapLoading: { flex: 1, alignItems: "center", justifyContent: "center", gap: spacing.sm },
  mapLoadingText: { ...typography.bodySmall },
  mapHint: { ...typography.caption, textAlign: "center", paddingVertical: spacing.xs },
  formContent: { padding: spacing.md, paddingBottom: spacing.xl, gap: spacing.sm },
  statusText: { ...typography.bodySmall },
  confirmButton: { marginTop: spacing.md, minHeight: 48, borderRadius: radius.md, alignItems: "center", justifyContent: "center" },
  confirmLabel: { fontWeight: "700", fontSize: 15 },
});

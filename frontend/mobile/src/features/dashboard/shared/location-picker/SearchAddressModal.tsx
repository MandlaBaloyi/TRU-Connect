import React, { useState } from "react";
import { ActivityIndicator, Alert, Modal, Pressable, StyleSheet, Text, View } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { useTheme } from "react-native-paper";
import { StatusBar } from "expo-status-bar";
import { X } from "lucide-react-native";

import { spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

import { SearchAddressBar } from "./components/SearchAddressBar";
import { useAddressSearch } from "./hooks/useAddressSearch";
import { retrieveAddress } from "./services/geocodingService";
import type { AddressSuggestion } from "./types";

interface Props {
  visible: boolean;
  onClose: () => void;
  /** Fires once a suggestion has been resolved to real coordinates --
   *  the caller's job from here is to open MapPickerModal with this
   *  as presetCenter, letting the business fine-tune the pin from a
   *  precise starting point rather than trusting Search Box's result
   *  blindly. This screen never sets a final delivery location on its
   *  own. */
  onLocationFound: (location: { latitude: number; longitude: number }) => void;
}

/**
 * SearchAddressModal -- a genuinely separate screen from
 * MapPickerModal, not a bar bolted onto the top of it. That combined
 * layout is exactly what live testing showed looking broken (the
 * suggestions dropdown fighting the map for the same cramped space).
 * DeliveryPaymentScreen now offers "Search your address" and "Choose
 * location on map" as two real, separate entry points -- this is the
 * first one. No map here at all; picking a result just resolves
 * coordinates and hands off to MapPickerModal via presetCenter.
 *
 * SafeAreaView imported from react-native-safe-area-context, NOT
 * react-native's own -- the core one is iOS-only, a genuine no-op on
 * Android (confirmed after a real device report of this exact
 * screen's header overlapping the status bar on Android). The
 * explicit <StatusBar> override exists for the same root cause on
 * the other axis: a full-screen Modal renders as its own top-level
 * window on Android, which doesn't inherit the app-level StatusBar
 * style set in app/_layout.tsx.
 */
export function SearchAddressModal({ visible, onClose, onLocationFound }: Props) {
  const theme = useTheme();
  const addressSearch = useAddressSearch();
  const [isRetrieving, setIsRetrieving] = useState(false);

  const handleClose = () => {
    addressSearch.completeSession();
    onClose();
  };

  const handleSelect = async (suggestion: AddressSuggestion) => {
    setIsRetrieving(true);
    try {
      const location = await retrieveAddress(suggestion.mapboxId, addressSearch.sessionToken);
      addressSearch.completeSession();
      onLocationFound(location);
      onClose();
    } catch {
      Alert.alert("Couldn't find that", "Try a different search, or use the map instead.");
    } finally {
      setIsRetrieving(false);
    }
  };

  return (
    <Modal visible={visible} animationType="slide" onRequestClose={handleClose}>
      {visible && <StatusBar style={theme.dark ? "light" : "dark"} />}
      <SafeAreaView style={[styles.safeArea, { backgroundColor: theme.colors.background }]}>
        <View style={[styles.header, { borderBottomColor: theme.colors.outline }]}>
          <Text style={[styles.headerTitle, { color: theme.colors.onSurface }]}>Search your address</Text>
          <Pressable onPress={handleClose} hitSlop={10} accessibilityRole="button" accessibilityLabel="Close">
            <X size={22} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
          </Pressable>
        </View>

        <View style={styles.content}>
          <SearchAddressBar
            query={addressSearch.query}
            onChangeQuery={addressSearch.setQuery}
            suggestions={addressSearch.suggestions}
            isLoading={addressSearch.isLoading || isRetrieving}
            onSelect={handleSelect}
          />
          <Text style={[styles.hint, { color: theme.colors.onSurfaceVariant }]}>
            Type your street or a landmark, then pick the closest match -- you'll get a chance to fine-tune the exact spot on
            the map next.
          </Text>
          {isRetrieving && (
            <View style={styles.retrievingRow}>
              <ActivityIndicator color={theme.colors.primary} />
              <Text style={{ color: theme.colors.onSurfaceVariant }}>Finding that address...</Text>
            </View>
          )}
        </View>
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
  content: { padding: spacing.md, gap: spacing.sm },
  hint: { ...typography.bodySmall },
  retrievingRow: { flexDirection: "row", alignItems: "center", gap: spacing.sm, paddingTop: spacing.sm },
});

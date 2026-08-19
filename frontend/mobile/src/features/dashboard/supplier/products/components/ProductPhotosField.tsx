/**
 * ProductPhotosField — multi-photo grid for Add Product, replacing the
 * single-image ProductImagePicker per review ("one image isn't
 * enough"). Real, on-device picking (expo-image-picker, same pattern
 * as the file it replaces) -- still entirely LOCAL, no Cloudinary
 * upload here. That's sub-goal 3's job; this component only produces
 * an ordered array of local URIs.
 *
 * FIRST PHOTO = COVER PHOTO, by position, not a separate flag -- see
 * types.ts's own Product.images docstring for the full reasoning. A
 * supplier never sees the word "primary" or "cover" as a concept to
 * manage; "Move to front" is the only control that changes it.
 *
 * REORDER/DELETE VIA LONG-PRESS, NOT DRAG -- true drag-and-drop
 * reordering would need a dedicated gesture library (this project has
 * react-native-gesture-handler/reanimated installed but no
 * draggable-flatlist equivalent) and is a reasonable amount of
 * additional surface for what "long-press -> choose an action" already
 * delivers functionally: move-to-front, delete. Flagged here
 * explicitly as a deliberate scope call, not an oversight -- full drag
 * reordering is a fine later polish request, not assumed to be
 * expected by default.
 *
 * TIER-AWARE LIMIT -- see algorithms/photoLimits.ts's own docstring
 * for why this takes a `tier` prop instead of resolving one internally
 * (subscription tier isn't real anywhere in the backend yet; every
 * caller today should pass "FREE" explicitly, which this component's
 * own default does, so nothing here pretends more exists than does).
 */

import React from "react";
import { Alert, Image, Pressable, StyleSheet, Text, View } from "react-native";
import { useTheme } from "react-native-paper";
import { Plus } from "lucide-react-native";
import * as ImagePicker from "expo-image-picker";

import type { SubscriptionTier } from "../algorithms/photoLimits";
import { getPhotoLimit } from "../algorithms/photoLimits";
import { radius, spacing } from "@/theme/spacing";
import { typography } from "@/theme/typography";

interface Props {
  localImageUris: string[];
  onChange: (uris: string[]) => void;
  tier?: SubscriptionTier;
}

async function pickFromCamera(): Promise<string | null> {
  const permission = await ImagePicker.requestCameraPermissionsAsync();
  if (!permission.granted) {
    Alert.alert("Camera access needed", "Allow camera access to take a photo.");
    return null;
  }
  const result = await ImagePicker.launchCameraAsync({ quality: 0.8, allowsEditing: true });
  if (result.canceled || result.assets.length === 0) return null;
  return result.assets[0].uri;
}

async function pickFromLibrary(): Promise<string | null> {
  const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
  if (!permission.granted) {
    Alert.alert("Photo library access needed", "Allow photo library access to choose a photo.");
    return null;
  }
  const result = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ["images"],
    quality: 0.8,
    allowsEditing: true,
  });
  if (result.canceled || result.assets.length === 0) return null;
  return result.assets[0].uri;
}

const TILE_SIZE = 88;

export function ProductPhotosField({ localImageUris, onChange, tier = "FREE" }: Props) {
  const theme = useTheme();
  const limit = getPhotoLimit(tier);
  const atLimit = localImageUris.length >= limit;

  const openAddPicker = () => {
    Alert.alert("Add product photo", undefined, [
      {
        text: "Take Photo",
        onPress: async () => {
          const uri = await pickFromCamera();
          if (uri) onChange([...localImageUris, uri]);
        },
      },
      {
        text: "Choose from Library",
        onPress: async () => {
          const uri = await pickFromLibrary();
          if (uri) onChange([...localImageUris, uri]);
        },
      },
      { text: "Cancel", style: "cancel" },
    ]);
  };

  const openPhotoActions = (index: number) => {
    const isCover = index === 0;
    const actions: { text: string; style?: "destructive" | "cancel"; onPress?: () => void }[] = [];
    if (!isCover) {
      actions.push({
        text: "Move to front (cover photo)",
        onPress: () => {
          const next = [...localImageUris];
          const [moved] = next.splice(index, 1);
          next.unshift(moved);
          onChange(next);
        },
      });
    }
    actions.push({
      text: "Remove photo",
      style: "destructive",
      onPress: () => onChange(localImageUris.filter((_, i) => i !== index)),
    });
    actions.push({ text: "Cancel", style: "cancel" });

    Alert.alert(isCover ? "Cover photo" : `Photo ${index + 1}`, undefined, actions);
  };

  return (
    <View style={styles.wrapper}>
      <View style={styles.grid}>
        {localImageUris.map((uri, index) => (
          <Pressable
            key={uri}
            onLongPress={() => openPhotoActions(index)}
            style={styles.tileWrapper}
            accessibilityRole="button"
            accessibilityLabel={
              index === 0 ? "Cover photo, long press for options" : `Photo ${index + 1}, long press for options`
            }
          >
            <Image source={{ uri }} style={styles.tile} />
            {index === 0 && (
              <View style={[styles.coverBadge, { backgroundColor: theme.colors.primary }]}>
                <Text style={[styles.coverBadgeText, { color: theme.colors.onPrimary }]}>Cover</Text>
              </View>
            )}
          </Pressable>
        ))}

        {!atLimit && (
          <Pressable
            onPress={openAddPicker}
            style={[styles.tile, styles.addTile, { borderColor: theme.colors.outline }]}
            accessibilityRole="button"
            accessibilityLabel="Add photo"
          >
            <Plus size={20} color={theme.colors.onSurfaceVariant} strokeWidth={2} />
            <Text style={[styles.addTileText, { color: theme.colors.onSurfaceVariant }]}>Add</Text>
          </Pressable>
        )}
      </View>

      <Text style={[styles.limitHint, { color: theme.colors.onSurfaceVariant }]}>
        {localImageUris.length} / {limit} photos
        {tier === "FREE" && atLimit ? " — upgrade for more" : ""}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  wrapper: { gap: spacing.xs },
  grid: { flexDirection: "row", flexWrap: "wrap", gap: spacing.sm },
  tileWrapper: { position: "relative" },
  tile: {
    width: TILE_SIZE,
    height: TILE_SIZE,
    borderRadius: radius.md,
  },
  addTile: {
    borderWidth: 1,
    borderStyle: "dashed",
    alignItems: "center",
    justifyContent: "center",
    gap: 4,
  },
  addTileText: { ...typography.caption },
  coverBadge: {
    position: "absolute",
    bottom: 4,
    left: 4,
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: radius.pill,
  },
  coverBadgeText: { ...typography.caption, fontWeight: "700" },
  limitHint: { ...typography.caption },
});

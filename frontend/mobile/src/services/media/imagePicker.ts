/**
 * On-device image picking -- the shared camera/library helpers, lifted
 * from features/dashboard/supplier/products/components/ProductPhotosField.tsx
 * (single-selection variant) so the profile/cover upload flow can use
 * the exact same behaviour without importing a product component.
 *
 * ENTIRELY LOCAL, no network -- returns a local file URI (or null on
 * cancel/permission-denied). Uploading is a separate step
 * (services/media/cloudinaryUpload.ts).
 *
 * No `allowsEditing` (forced crop) -- same call ProductPhotosField
 * already made: a crop step before every upload was confusing (unclear
 * which button finished it) and redundant, since the backend fits
 * every image to a consistent size on ingest (max_dimension_px in the
 * signed transformation).
 */
import { Alert } from "react-native";
import * as ImagePicker from "expo-image-picker";

export type ImageSource = "CAMERA" | "LIBRARY";

export async function pickImageFromCamera(): Promise<string | null> {
  const permission = await ImagePicker.requestCameraPermissionsAsync();
  if (!permission.granted) {
    Alert.alert("Camera access needed", "Allow camera access to take a photo.");
    return null;
  }
  const result = await ImagePicker.launchCameraAsync({ quality: 0.8 });
  if (result.canceled || result.assets.length === 0) return null;
  return result.assets[0].uri;
}

export async function pickImageFromLibrary(): Promise<string | null> {
  const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
  if (!permission.granted) {
    Alert.alert("Photo library access needed", "Allow photo library access to choose a photo.");
    return null;
  }
  const result = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ["images"],
    quality: 0.8,
  });
  if (result.canceled || result.assets.length === 0) return null;
  return result.assets[0].uri;
}

export async function pickImage(source: ImageSource): Promise<string | null> {
  return source === "CAMERA" ? pickImageFromCamera() : pickImageFromLibrary();
}

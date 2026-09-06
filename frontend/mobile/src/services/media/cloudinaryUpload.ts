/**
 * uploadToCloudinary -- the one function in this whole app that
 * actually sends image bytes over the network to Cloudinary, straight
 * from the device. Never touches TRU Connect's own backend -- that's
 * the entire point of the signed-upload design (see backend's own
 * shared/media/providers/cloudinary_provider.py docstring): Flask
 * never carries image bytes.
 *
 * SHARED, not product-specific -- lives under src/services/media/ now
 * (moved from features/dashboard/supplier/products/services/) because
 * the supplier profile/cover image upload uses the exact same signed
 * flow.
 *
 * USES expo-file-system's native File.upload(), NOT fetch() + FormData.
 * REAL BUG FOUND ON DEVICE (Expo SDK 57 / RN 0.86): SDK 54+ replaces
 * the global fetch/FormData with the WinterCG implementation
 * (expo/src/winter/fetch/convertFormData.ts), which does NOT accept
 * React Native's classic `{ uri, name, type }` file-part shape -- it
 * throws "Unsupported FormDataPart implementation" and the upload
 * never leaves the phone (confirmed: no request ever reached
 * Cloudinary, no webhook fired). File.upload() is the sanctioned
 * replacement: a native multipart POST that streams the file directly,
 * no JS FormData, no whole-image-in-memory. Every param below is sent
 * as a string form field, exactly as the backend signed it.
 *
 * Every param sent here must EXACTLY match what the backend signed --
 * timestamp, public_id, allowed_formats, transformation, asset_folder,
 * notification_url. Cloudinary recomputes the signature server-side
 * from whatever it actually received; a mismatch on ANY of these fails
 * the upload with a signature error, not a silent fallback.
 */
import { File, UploadType } from "expo-file-system";

export interface CloudinarySignedUpload {
  cloudName: string;
  apiKey: string;
  timestamp: number;
  signature: string;
  publicId: string;
  uploadUrl: string;
  allowedFormats: string;
  transformation: string;
  // Empty string when the backend hasn't got a webhook URL configured
  // yet (e.g. no tunnel running during local dev) -- omitted from the
  // request entirely in that case, matching exactly what the backend
  // signed. Sending it when the backend DIDN'T sign it (or vice
  // versa) would make Cloudinary reject the whole upload as an
  // invalid signature, not just skip the notification.
  notificationUrl: string;
  // "perception_point" when malware scanning is currently active
  // (CLOUDINARY_MODERATION_ENABLED on the backend), "" when it's been
  // deliberately turned off. Same signature rule as notificationUrl.
  moderation: string;
  // NOT the same field as publicId's own path, even though it's built
  // from the identical string -- Cloudinary treats public_id (the
  // asset's permanent URL) and asset_folder (where it shows up in the
  // Media Library UI) as independent concepts. Must be echoed exactly.
  assetFolder: string;
}

export interface CloudinaryUploadResult {
  publicId: string;
  secureUrl: string;
  resourceType: string;
  format: string | null;
  width: number | null;
  height: number | null;
  bytes: number | null;
}

export async function uploadToCloudinary(
  signed: CloudinarySignedUpload,
  localUri: string
): Promise<CloudinaryUploadResult> {
  // Every multipart form field Cloudinary needs alongside the file,
  // each as a string, echoed exactly as the backend signed it. The
  // file itself is attached by File.upload() under fieldName "file".
  const parameters: Record<string, string> = {
    api_key: signed.apiKey,
    timestamp: String(signed.timestamp),
    signature: signed.signature,
    public_id: signed.publicId,
    allowed_formats: signed.allowedFormats,
    transformation: signed.transformation,
    asset_folder: signed.assetFolder,
  };
  if (signed.notificationUrl) {
    parameters.notification_url = signed.notificationUrl;
  }
  if (signed.moderation) {
    parameters.moderation = signed.moderation;
  }

  const file = new File(localUri);

  let result: { status: number; body: string };
  try {
    result = await file.upload(signed.uploadUrl, {
      httpMethod: "POST",
      uploadType: UploadType.MULTIPART,
      fieldName: "file",
      parameters,
    });
  } catch (networkError) {
    throw new Error(
      networkError instanceof Error
        ? `Couldn't reach Cloudinary: ${networkError.message}`
        : "Couldn't reach Cloudinary. Check your connection."
    );
  }

  let data: any;
  try {
    data = JSON.parse(result.body);
  } catch {
    throw new Error(`Cloudinary returned a non-JSON ${result.status} response.`);
  }

  if (result.status < 200 || result.status >= 300) {
    // Cloudinary's own error envelope: { error: { message } }.
    throw new Error(data?.error?.message || "Image upload failed. Check your connection and try again.");
  }

  return {
    publicId: data.public_id,
    secureUrl: data.secure_url,
    resourceType: data.resource_type,
    format: data.format ?? null,
    width: data.width ?? null,
    height: data.height ?? null,
    bytes: data.bytes ?? null,
  };
}

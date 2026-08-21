/**
 * uploadToCloudinary -- the one function in this whole app that
 * actually sends image bytes over the network to Cloudinary, straight
 * from the device. Never touches TRU Connect's own backend -- that's
 * the entire point of the signed-upload design (see backend's own
 * shared/media/providers/cloudinary_provider.py docstring): Flask
 * never carries image bytes.
 *
 * Every param sent here must EXACTLY match what the backend signed --
 * timestamp, public_id, allowed_formats, transformation. Cloudinary
 * recomputes the signature server-side from whatever it actually
 * received; a mismatch on ANY of these fails the upload with a
 * signature error, not a silent fallback.
 *
 * Deliberately generic (CloudinarySignedUpload in, CloudinaryUploadResult
 * out) -- no product/supplier knowledge here at all, so this same
 * function will serve a future profile-photo or verification-document
 * upload without changes, matching the backend's own MediaProvider
 * abstraction one layer down.
 */

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
  const filename = localUri.split("/").pop() || "photo.jpg";

  // React Native's own FormData/fetch understand this {uri, name, type}
  // shape for a file field -- not a real Blob, but the RN networking
  // layer knows to stream the file at `uri` directly, which is what
  // keeps this from ever loading the whole image into JS memory first.
  const formData = new FormData();
  formData.append("file", { uri: localUri, name: filename, type: "image/jpeg" } as unknown as Blob);
  formData.append("api_key", signed.apiKey);
  formData.append("timestamp", String(signed.timestamp));
  formData.append("signature", signed.signature);
  formData.append("public_id", signed.publicId);
  formData.append("allowed_formats", signed.allowedFormats);
  formData.append("transformation", signed.transformation);
  if (signed.notificationUrl) {
    formData.append("notification_url", signed.notificationUrl);
  }

  const response = await fetch(signed.uploadUrl, { method: "POST", body: formData });
  const data = await response.json();

  if (!response.ok) {
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

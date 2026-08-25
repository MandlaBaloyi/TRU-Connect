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
  // "perception_point" when malware scanning is currently active
  // (CLOUDINARY_MODERATION_ENABLED on the backend), "" when it's been
  // deliberately turned off (e.g. free-tier scan quota, or before
  // real launch capital is in place). Same signature rule as
  // notificationUrl -- must be echoed exactly as signed, or omitted
  // exactly when it was omitted.
  moderation: string;
  // NOT the same field as publicId's own path, even though it's built
  // from the identical string -- Cloudinary treats public_id (the
  // asset's permanent URL) and asset_folder (purely where it shows up
  // in the browsable Media Library UI) as genuinely independent
  // concepts. Must be echoed exactly, same signature rule as every
  // other field here -- omitting it (a real gap found during review)
  // meant every upload was fully find-able by search but invisible in
  // the Folders tree on this account's Dynamic Folder Mode.
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
  const filename = localUri.split("/").pop() || "photo.jpg";

  // REAL BUG FOUND DURING CODE REVIEW: this used to hardcode
  // type: "image/jpeg" for every upload, regardless of what the file
  // actually was -- a PNG or WEBP would still be labeled "image/jpeg"
  // in the multipart request. Cloudinary very likely detects the real
  // format from the file's own bytes rather than trusting this label,
  // which is probably why it never caused a visible failure -- but
  // the label itself was simply wrong. Derived from the real
  // extension now, with a sane fallback for anything unrecognised.
  const extension = filename.split(".").pop()?.toLowerCase();
  const mimeTypeByExtension: Record<string, string> = {
    jpg: "image/jpeg",
    jpeg: "image/jpeg",
    png: "image/png",
    webp: "image/webp",
  };
  const mimeType = (extension && mimeTypeByExtension[extension]) || "image/jpeg";

  // React Native's own FormData/fetch understand this {uri, name, type}
  // shape for a file field -- not a real Blob, but the RN networking
  // layer knows to stream the file at `uri` directly, which is what
  // keeps this from ever loading the whole image into JS memory first.
  const formData = new FormData();
  formData.append("file", { uri: localUri, name: filename, type: mimeType } as unknown as Blob);
  formData.append("api_key", signed.apiKey);
  formData.append("timestamp", String(signed.timestamp));
  formData.append("signature", signed.signature);
  formData.append("public_id", signed.publicId);
  formData.append("allowed_formats", signed.allowedFormats);
  formData.append("transformation", signed.transformation);
  if (signed.notificationUrl) {
    formData.append("notification_url", signed.notificationUrl);
  }
  if (signed.moderation) {
    formData.append("moderation", signed.moderation);
  }
  formData.append("asset_folder", signed.assetFolder);

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

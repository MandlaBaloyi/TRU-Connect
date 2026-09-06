/**
 * Supplier profile / cover image upload -- REAL, signed
 * direct-to-Cloudinary, scoped to this supplier's own folder on the
 * backend. Replaces the old mock in fileRepository.ts
 * (getProfileImage/setProfileImage/getCoverImage/setCoverImage) and
 * the separate ProfileImageScreen it fed.
 *
 * Orchestrated exactly like products' own
 * httpProductsApi.uploadProductImagesBestEffort: ask the backend to
 * sign an upload, push the bytes straight to Cloudinary, then register
 * the result. Flask never carries the image bytes. The backend writes
 * the approved secure_url onto SupplierProfile
 * (business_image_url / cover_image_url), which GET /my-profile then
 * returns -- so the displayed image is always whatever the profile
 * says, never local device state.
 *
 * USE_MOCK: same switch as accountService.ts -- in mock mode there's
 * no backend to sign anything, so the picked local URI is echoed back
 * and the screen just shows that.
 */
import { apiDelete, apiPost } from "@/services/api/apiClient";
import { uploadToCloudinary, type CloudinarySignedUpload } from "@/services/media/cloudinaryUpload";

export type ProfileImageSlot = "profile" | "cover";

const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

interface SignedUploadDto {
  cloud_name: string;
  api_key: string;
  timestamp: number;
  signature: string;
  public_id: string;
  upload_url: string;
  allowed_formats: string;
  transformation: string;
  notification_url: string;
  moderation: string;
  asset_folder: string;
}

async function requestUploadSignature(slot: ProfileImageSlot): Promise<CloudinarySignedUpload> {
  const data = await apiPost<SignedUploadDto>("/supplier-discovery/my-profile/images/upload-signature", { slot });
  return {
    cloudName: data.cloud_name,
    apiKey: data.api_key,
    timestamp: data.timestamp,
    signature: data.signature,
    publicId: data.public_id,
    uploadUrl: data.upload_url,
    allowedFormats: data.allowed_formats,
    transformation: data.transformation,
    notificationUrl: data.notification_url,
    moderation: data.moderation,
    assetFolder: data.asset_folder,
  };
}

/**
 * Uploads a picked local image for one slot and returns the stored
 * secure URL. Throws on failure (unlike products' best-effort
 * per-photo loop -- here there's exactly one image and the caller
 * wants to know if it didn't make it).
 */
export async function uploadProfileImage(slot: ProfileImageSlot, localUri: string): Promise<{ secureUrl: string }> {
  if (USE_MOCK) {
    return { secureUrl: localUri };
  }

  const signed = await requestUploadSignature(slot);
  const uploaded = await uploadToCloudinary(signed, localUri);
  const registered = await apiPost<{ slot: string; secureUrl: string; scanStatus: string }>(
    "/supplier-discovery/my-profile/images",
    {
      slot,
      cloudinary_public_id: uploaded.publicId,
      secure_url: uploaded.secureUrl,
      resource_type: uploaded.resourceType,
      format: uploaded.format,
      width: uploaded.width,
      height: uploaded.height,
      bytes: uploaded.bytes,
    }
  );
  return { secureUrl: registered.secureUrl };
}

export async function removeProfileImage(slot: ProfileImageSlot): Promise<void> {
  if (USE_MOCK) return;
  await apiDelete(`/supplier-discovery/my-profile/images/${slot}`);
}

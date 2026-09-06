/**
 * FileRepository — the provider-neutral file/upload boundary (file.txt
 * §10). Currently used by the profile-image flow; written generically
 * enough to be the same boundary the future Stock Order feature's
 * proof-of-payment upload reuses once that exists, rather than that
 * feature inventing its own — see this file's note further down on
 * why its document-picker path was removed for now instead of kept
 * with no caller.
 *
 * selectFile() wraps expo-image-picker — genuinely real, on-device, no
 * network. Everything past that point (uploadFile/getFileStatus/
 * deleteFile/getDownloadUrl) is MOCK-BACKED, same discipline as
 * accountService.ts: replace the function body, not the signature,
 * when a real upload-session backend exists (see types.ts's
 * documented future endpoints).
 *
 * ============================================================
 * WHAT THIS FILE DELIBERATELY DOES NOT DO
 * ============================================================
 * It does not scan for malware. It does not validate magic bytes. It
 * does not decide whether a file is "safe". Those are the future
 * backend's job (file.txt §7, §8, §23) — this file only ever narrows
 * the on-device PICKER to plausible types, which is a UX convenience,
 * NOT a security boundary, and is documented as such at each point
 * below so nobody mistakes an accept-type filter for validation.
 *
 * NOTE: expo-image-picker calls below were verified directly against
 * the published 17.0.11 package (downloaded and checked against its
 * real .d.ts files — node_modules wasn't present in the environment
 * this was written in, so the package was fetched from the registry
 * instead, to satisfy this project's own house rule of verifying
 * against the real API rather than training-data memory). One real
 * finding from that check: `ImagePicker.MediaTypeOptions` is
 * deprecated in 17.x in favour of a `MediaType[]` array — used below
 * accordingly, not the deprecated form.
 *
 * DOCUMENT PICKING (PDF support via expo-document-picker) was removed
 * from this file — it existed only for the payment-proof flow, which
 * has moved out of My Account's scope (see types.ts's note above
 * PaymentMethodType: proof-of-payment belongs to the future Stock
 * Order feature, once a business can actually choose Cash/EFT for a
 * specific stock order). Rather than leave a picker path with no
 * caller anywhere in the app, it's removed for now. It was verified
 * working against the real expo-document-picker 14.0.8 package before
 * removal, so bringing it back when Stock Order needs it is a known
 * quantity, not a fresh unknown.
 */
import * as ImagePicker from "expo-image-picker";

import type { FileAsset, UploadSession, UploadStatus } from "../types";

const latency = (ms = 350) => new Promise<void>((resolve) => setTimeout(resolve, ms));

function generateId(prefix: string): string {
  return `${prefix}_${Math.random().toString(36).slice(2, 10)}`;
}

export class FileRepositoryError extends Error {
  code: "CANCELLED" | "PERMISSION_DENIED" | "UPLOAD_FAILED";
  constructor(message: string, code: FileRepositoryError["code"]) {
    super(message);
    this.name = "FileRepositoryError";
    this.code = code;
  }
}

export type SelectSource = "CAMERA" | "LIBRARY";

/**
 * Opens the appropriate native picker and returns a local, unuploaded
 * FileAsset (status: "selected"). Never touches the network.
 *
 * The accept filter is images only — a UX convenience matching what
 * these pickers are for, not a security control. Whatever is actually
 * inside the selected file is for the future backend's magic-byte
 * validation to determine, never this function (file.txt §24: never
 * trust extension or client MIME type).
 */
export async function selectFile(source: SelectSource): Promise<FileAsset> {
  if (source === "CAMERA") {
    const permission = await ImagePicker.requestCameraPermissionsAsync();
    if (!permission.granted) {
      throw new FileRepositoryError("Camera access is needed to take a photo.", "PERMISSION_DENIED");
    }
    const result = await ImagePicker.launchCameraAsync({ quality: 0.8, allowsEditing: true });
    return fromImagePickerResult(result);
  }

  const permission = await ImagePicker.requestMediaLibraryPermissionsAsync();
  if (!permission.granted) {
    throw new FileRepositoryError("Photo library access is needed to choose a photo.", "PERMISSION_DENIED");
  }
  const result = await ImagePicker.launchImageLibraryAsync({
    mediaTypes: ["images"],
    quality: 0.8,
    allowsEditing: true,
  });
  return fromImagePickerResult(result);
}

function fromImagePickerResult(result: ImagePicker.ImagePickerResult): FileAsset {
  if (result.canceled || result.assets.length === 0) {
    throw new FileRepositoryError("Selection cancelled.", "CANCELLED");
  }
  const asset = result.assets[0];
  const fileName = asset.fileName ?? `photo-${Date.now()}.jpg`;
  return {
    id: null,
    localUri: asset.uri,
    kind: "IMAGE",
    fileName,
    sizeBytes: asset.fileSize ?? null,
    status: "selected",
    statusMessage: null,
    createdAt: new Date().toISOString(),
  };
}

// ---------------------------------------------------------------------------
// MOCK-BACKED past this point (see file docstring). In-memory session
// registry so getFileStatus/deleteFile have something real to look up
// against within a session, same pattern as accountService's module-
// scope state.
// ---------------------------------------------------------------------------

const sessionRegistry = new Map<string, FileAsset>();

/**
 * Simulates: request upload authorization -> upload -> quarantine ->
 * scanning -> validation -> approved storage (file.txt §9's own
 * diagram). Returns an UploadSession the caller polls/observes via
 * onProgress; the FINAL status is either "approved" or "rejected" —
 * never assumed to be "approved" just because the transfer finished.
 *
 * The mock intentionally rejects nothing on its own (there is no real
 * scanner here to make that call) — it always resolves to "approved"
 * after passing through "uploading" and "processing", so the UI states
 * are genuinely exercised without this file pretending to be a
 * security decision it has no authority to make.
 */
export async function uploadFile(
  asset: FileAsset,
  onProgress?: (session: UploadSession) => void
): Promise<FileAsset> {
  const sessionId = generateId("upl");
  const id = generateId("file");

  const emit = (status: UploadStatus, progressPercent: number, statusMessage: string | null = null) => {
    const next: FileAsset = { ...asset, id, status, statusMessage };
    onProgress?.({ sessionId, asset: next, progressPercent });
    return next;
  };

  emit("uploading", 0);
  await latency(250);
  emit("uploading", 60);
  await latency(250);
  emit("uploading", 100);

  await latency(200);
  emit("processing", 100, "Checking file...");
  await latency(500);

  const approved = emit("approved", 100);
  sessionRegistry.set(id, approved);
  return approved;
}

export async function getFileStatus(id: string): Promise<FileAsset> {
  await latency(150);
  const found = sessionRegistry.get(id);
  if (!found) {
    throw new FileRepositoryError("This file could not be found.", "UPLOAD_FAILED");
  }
  return found;
}

export async function deleteFile(id: string): Promise<void> {
  await latency(150);
  sessionRegistry.delete(id);
}

/**
 * A real backend would return a short-lived SIGNED url here (file.txt
 * §8: temporary signed access URLs, never a public bucket). The mock
 * just echoes the local URI when it's still available in this session
 * — there is no persistent storage to point to.
 */
export async function getDownloadUrl(asset: FileAsset): Promise<string | null> {
  await latency(100);
  return asset.localUri;
}

// ---------------------------------------------------------------------------
// The supplier profile photo / cover banner USED to be mocked here
// (getProfileImage/setProfileImage/getCoverImage/setCoverImage). They
// are now REAL — uploaded straight to Cloudinary via a backend-signed
// upload and stored on SupplierProfile. See
// services/profileImageUpload.ts and hooks/useProfileImageUpload.ts.
// selectFile/uploadFile above stay: the future stock-order
// proof-of-payment flow reuses this same provider-neutral boundary.
// ---------------------------------------------------------------------------

/**
 * formDataFilePart -- a multipart file part that the Expo SDK 54+
 * WinterCG FormData / fetch actually accepts.
 *
 * REAL BUG (Expo SDK 57 / RN 0.86): SDK 54+ patches the global
 * FormData and replaces global fetch with the WinterCG implementation.
 * Its multipart serializer
 * (expo/src/winter/fetch/convertFormData.ts) only handles three part
 * shapes: a plain string, a `Blob` instance, or an object exposing an
 * async `bytes()` method. React Native's classic
 * `{ uri, name, type }` file shape is none of those, so it throws
 * "Unsupported FormDataPart implementation" and the request never
 * leaves the device.
 *
 * This returns the third accepted shape: `{ name, type, bytes() }`.
 * `getFormDataPartHeaders` reads `name` (→ filename) and `type` (→
 * Content-Type); the serializer calls `bytes()` for the body.
 * `expo-file-system`'s `File.arrayBuffer()` reads the file off disk.
 *
 * For a SINGLE file going to Cloudinary, prefer the native streaming
 * `File.upload()` (see cloudinaryUpload.ts). This helper is for the
 * cases that genuinely need a hand-built multipart body -- e.g. bulk
 * import sending a spreadsheet + a ZIP in one request.
 */
import { File } from "expo-file-system";

export interface FormDataFilePart {
  name: string;
  type: string;
  bytes: () => Promise<Uint8Array>;
}

export function formDataFilePart(uri: string, filename: string, type: string): FormDataFilePart {
  const file = new File(uri);
  return {
    name: filename,
    type,
    bytes: async () => new Uint8Array(await file.arrayBuffer()),
  };
}

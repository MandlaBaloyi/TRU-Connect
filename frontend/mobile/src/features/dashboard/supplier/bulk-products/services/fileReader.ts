/**
 * Thin wrapper around expo-file-system's (v19+) File class. Isolated
 * in its own file specifically so if expo-file-system's API changes
 * again, only this one file needs updating -- every parser below reads
 * through these two functions, never expo-file-system directly.
 */

import { File } from "expo-file-system";

/** UTF-8 text -- CSV files. */
export async function readFileAsText(uri: string): Promise<string> {
  const file = new File(uri);
  return await file.text();
}

/** Base64 -- binary formats (XLSX, ZIP) that papaparse-style text
 *  reading would corrupt. Synchronous on the native side. */
export function readFileAsBase64(uri: string): string {
  const file = new File(uri);
  return file.base64();
}

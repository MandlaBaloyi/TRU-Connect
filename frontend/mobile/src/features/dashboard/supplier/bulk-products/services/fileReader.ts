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
 *  reading would corrupt. Genuinely synchronous: base64Sync(), NOT
 *  base64().
 *
 *  REAL BUG FOUND DURING DEVICE TESTING, CONFIRMED DIRECTLY AGAINST
 *  THE INSTALLED PACKAGE, NOT GUESSED -- expo-file-system's own type
 *  declarations for File.base64() are self-contradictory: the return
 *  type says `string` (synchronous), but the method's own docstring
 *  says "A promise that resolves with...". At runtime it IS async,
 *  matching the docstring, not the type. Calling it without `await`
 *  (as this file previously did, because the incorrect type told
 *  TypeScript that was fine) meant XLSX.read() received a Promise
 *  object instead of a real base64 string, and SheetJS's own parsing
 *  crashed trying to call a string method (.slice) on it -- exactly
 *  the "f.slice is not a function" error hit during real testing.
 *  base64Sync() has no such contradiction: its type AND its own
 *  docstring both agree it returns a plain string synchronously. */
export function readFileAsBase64(uri: string): string {
  const file = new File(uri);
  return file.base64Sync();
}

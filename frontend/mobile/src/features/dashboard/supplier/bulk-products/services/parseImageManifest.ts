/**
 * parseImageManifest.ts — genuinely reads the filenames inside the
 * uploaded ZIP (JSZip), so "image not found" errors in the preview are
 * checked against what's actually in the file, not assumed.
 * DELIBERATELY DOES NOT EXTRACT OR DECODE IMAGE BYTES -- listing
 * entries is enough for the preview's matching step; real
 * extraction/validation (magic bytes, malware scan, Cloudinary
 * upload) is backend work per this feature's own security-pipeline
 * design, not something to fake client-side.
 */

import JSZip from "jszip";

import type { ImportImageManifest } from "../types";
import { readFileAsBase64 } from "./fileReader";

const IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".webp"];

function basename(path: string): string {
  return path.split("/").pop() ?? path;
}

function hasImageExtension(fileName: string): boolean {
  const lower = fileName.toLowerCase();
  return IMAGE_EXTENSIONS.some((ext) => lower.endsWith(ext));
}

export async function parseImageManifest(uri: string, fileName: string): Promise<ImportImageManifest> {
  const base64 = readFileAsBase64(uri);
  const zip = await JSZip.loadAsync(base64, { base64: true });

  const entries: string[] = [];
  zip.forEach((relativePath, entry) => {
    if (entry.dir) return;
    const name = basename(relativePath);
    // Skip macOS's own __MACOSX metadata folder and hidden files --
    // an extremely common accidental inclusion when someone zips a
    // folder on a Mac, not a real image reference.
    if (relativePath.startsWith("__MACOSX/") || name.startsWith(".")) return;
    if (!hasImageExtension(name)) return;
    entries.push(name);
  });

  return { fileName, entries };
}

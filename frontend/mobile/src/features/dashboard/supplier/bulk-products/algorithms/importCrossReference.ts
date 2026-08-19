/**
 * Cross-references each row's image references against what's
 * actually in the uploaded ZIP, and rolls up the preview counts.
 * Mutates nothing -- returns a NEW ParsedImportFile with image errors
 * merged in, same "never mutate, always return" discipline as
 * bulk-products' own applyPriceAdjustment.
 */

import type { ImportImageManifest, ImportPreviewSummary, ParsedImportFile, ParsedImportRow } from "../types";

function basename(path: string): string {
  return path.split("/").pop() ?? path;
}

function isImageMatched(filename: string, manifest: ImportImageManifest | null): boolean {
  if (!manifest) return false;
  const target = basename(filename).toLowerCase();
  return manifest.entries.some((entry) => basename(entry).toLowerCase() === target);
}

export function applyImageManifest(file: ParsedImportFile, manifest: ImportImageManifest | null): ParsedImportFile {
  const rows: ParsedImportRow[] = file.rows.map((row) => {
    if (row.imageReferences.length === 0) return row;

    const imageErrors = row.imageReferences
      .filter((ref) => !isImageMatched(ref.filename, manifest))
      .map((ref) => ({
        field: ref.column,
        message: manifest
          ? `Image not found in ZIP: "${ref.filename}".`
          : `Image referenced ("${ref.filename}") but no ZIP was uploaded.`,
      }));

    if (imageErrors.length === 0) return row;
    return { ...row, errors: [...row.errors, ...imageErrors] };
  });

  return { ...file, rows };
}

export function computePreviewSummary(file: ParsedImportFile, manifest: ImportImageManifest | null): ImportPreviewSummary {
  let validRows = 0;
  let errorRows = 0;
  let totalImageReferences = 0;
  let matchedImages = 0;

  for (const row of file.rows) {
    if (row.errors.length === 0) validRows += 1;
    else errorRows += 1;

    for (const ref of row.imageReferences) {
      totalImageReferences += 1;
      if (isImageMatched(ref.filename, manifest)) matchedImages += 1;
    }
  }

  return {
    totalRows: file.rows.length,
    validRows,
    errorRows,
    totalImageReferences,
    matchedImages,
    missingImages: totalImageReferences - matchedImages,
  };
}

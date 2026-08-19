/**
 * parseSpreadsheet.ts — REAL parsing, not a mock. papaparse for CSV,
 * SheetJS (xlsx) for XLSX -- both genuinely read the file the supplier
 * picked and produce the exact ParsedImportFile shape the preview
 * screen renders. This is deliberately real on the client (per
 * review: "it should parse a real CSV/XLSX file client-side so I can
 * review it easily") while staying BACKEND-READY: the same
 * importColumns.ts spec and rowValidator.ts logic this file calls are
 * exactly what the real backend's own parser needs to reimplement
 * (Python, not JS, but the same column contract and the same
 * validation rules) once Import Products is wired to a real endpoint
 * -- nothing here is throwaway.
 */

import Papa from "papaparse";
import * as XLSX from "xlsx";

import type { ImportSourceType, ParsedImportFile } from "../types";
import { KNOWN_COLUMN_HEADERS, REQUIRED_COLUMN_HEADERS } from "./importColumns";
import { validateRow } from "./rowValidator";
import { readFileAsBase64, readFileAsText } from "./fileReader";

function normalizeHeader(header: string): string {
  return header.trim().toLowerCase();
}

function buildParsedFile(
  sourceType: ImportSourceType,
  fileName: string,
  rawHeaders: string[],
  records: Record<string, unknown>[]
): ParsedImportFile {
  const columnHeaders = rawHeaders.map(normalizeHeader).filter(Boolean);
  const missingRequiredColumns = REQUIRED_COLUMN_HEADERS.filter((h) => !columnHeaders.includes(h));
  const unrecognizedColumns = columnHeaders.filter((h) => !KNOWN_COLUMN_HEADERS.includes(h));

  const rows = records.map((record, index) => {
    const normalizedRecord: Record<string, string> = {};
    for (const [key, value] of Object.entries(record)) {
      normalizedRecord[normalizeHeader(key)] = value === null || value === undefined ? "" : String(value).trim();
    }
    // +2: row 1 is the header row, so the first data row is row 2 --
    // matches what the supplier sees if they open the file themselves,
    // which is what the error report needs to say ("Row 143: ...").
    return validateRow(normalizedRecord, index + 2);
  });

  return { sourceType, fileName, rows, columnHeaders, unrecognizedColumns, missingRequiredColumns };
}

export async function parseCsvFile(uri: string, fileName: string): Promise<ParsedImportFile> {
  const content = await readFileAsText(uri);
  const result = Papa.parse<Record<string, string>>(content, {
    header: true,
    skipEmptyLines: true,
  });
  const headers = result.meta.fields ?? [];
  return buildParsedFile("CSV", fileName, headers, result.data);
}

export async function parseXlsxFile(uri: string, fileName: string): Promise<ParsedImportFile> {
  const base64 = readFileAsBase64(uri);
  const workbook = XLSX.read(base64, { type: "base64" });
  const firstSheetName = workbook.SheetNames[0];
  if (!firstSheetName) {
    return buildParsedFile("XLSX", fileName, [], []);
  }
  const sheet = workbook.Sheets[firstSheetName];

  // Header row read separately (array form) so it's known even if the
  // sheet has zero data rows -- the object form below would give an
  // empty array with no header info at all in that case.
  const headerRow = (XLSX.utils.sheet_to_json(sheet, { header: 1, raw: true })[0] as unknown[]) ?? [];
  const headers = headerRow.map((h) => (h === undefined || h === null ? "" : String(h)));

  const records = XLSX.utils.sheet_to_json<Record<string, unknown>>(sheet, { defval: "", raw: true });
  return buildParsedFile("XLSX", fileName, headers, records);
}

export async function parseSpreadsheetFile(uri: string, fileName: string): Promise<ParsedImportFile> {
  const extension = fileName.split(".").pop()?.toLowerCase();
  if (extension === "csv") return parseCsvFile(uri, fileName);
  if (extension === "xlsx" || extension === "xls") return parseXlsxFile(uri, fileName);
  throw new Error(`Unsupported file type: .${extension ?? "unknown"}. Upload a .csv or .xlsx file.`);
}

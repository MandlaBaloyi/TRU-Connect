/**
 * Bulk Import — mock implementation. Reuses the EXISTING mock
 * Products/Inventory creation (via those features' own switchers,
 * which resolve back to their own mock implementations since we're
 * already in mock mode by definition here) -- same "one shared
 * creation path, not a bulk-only copy" principle the real backend's
 * own worker follows (see backend's import_worker.py docstring).
 *
 * NO SERVER TO RE-PARSE AGAINST -- unlike httpBulkImportApi.ts, this
 * implementation genuinely needs the client's own already-parsed rows
 * (there's no backend here to re-validate independently), so
 * submitImport's third parameter is actually used here, not ignored.
 *
 * RUNS SYNCHRONOUSLY, NOT AS A SIMULATED BACKGROUND JOB -- the stored
 * job is already COMPLETED by the time submitImport resolves. Simpler
 * than simulating a multi-poll progression, and mock mode's own value
 * is exercising the UI/data flow, not proving async timing.
 */
import { createProduct } from "../../products/api/productsApi";
import { adjustStock } from "../../inventory/api/inventoryApi";
import type { ImportJob, ImportJobError, ParsedImportFile } from "../types";
import type { PickedFile } from "../services/importSession";

function mockId(): string {
  return `mock-import-${Date.now()}-${Math.random().toString(36).slice(2, 8)}`;
}

function nowIso(): string {
  return new Date().toISOString();
}

const jobs = new Map<string, ImportJob>();
const jobErrors = new Map<string, ImportJobError[]>();

export async function submitImport(
  spreadsheetFile: PickedFile,
  zipFile: PickedFile | null,
  parsedFile: ParsedImportFile
): Promise<ImportJob> {
  const id = mockId();
  const validRows = parsedFile.rows.filter((row) => row.errors.length === 0);
  const errorRows = parsedFile.rows.filter((row) => row.errors.length > 0);

  let createdCount = 0;
  for (const row of validRows) {
    if (!row.name || !row.category || row.priceCents === null || !row.sellingUnit) continue;
    const product = await createProduct({
      name: row.name,
      category: row.category,
      priceCents: row.priceCents,
      sellingUnit: row.sellingUnit,
      localImageUris: [], // mock mode never simulates the image-match-and-upload step
    });
    createdCount += 1;

    if (row.quantity && row.quantity > 0) {
      await adjustStock({ productId: product.id, quantityDelta: row.quantity, reason: "STOCK_RECEIVED" });
    }
  }

  const job: ImportJob = {
    id,
    status: "COMPLETED",
    sourceFilename: spreadsheetFile.name,
    hasImagesZip: zipFile !== null,
    totalRows: parsedFile.rows.length,
    validRows: validRows.length,
    errorRows: errorRows.length,
    createdRows: createdCount,
    imagesTotal: parsedFile.rows.reduce((sum, r) => sum + r.imageReferences.length, 0),
    imagesMatched: 0, // mock never simulates real image upload/matching
    failureReason: null,
    createdAt: nowIso(),
    completedAt: nowIso(),
  };

  jobs.set(id, job);
  jobErrors.set(
    id,
    errorRows.flatMap((row) =>
      row.errors.map((e) => ({ rowNumber: row.rowNumber, field: e.field, message: e.message }))
    )
  );

  return job;
}

export async function getImportJob(jobId: string): Promise<ImportJob> {
  const job = jobs.get(jobId);
  if (!job) throw new Error("Import job not found.");
  return job;
}

export async function getImportJobErrors(jobId: string): Promise<ImportJobError[]> {
  return jobErrors.get(jobId) ?? [];
}

export async function listImportJobs(): Promise<ImportJob[]> {
  return Array.from(jobs.values()).sort((a, b) => b.createdAt.localeCompare(a.createdAt));
}

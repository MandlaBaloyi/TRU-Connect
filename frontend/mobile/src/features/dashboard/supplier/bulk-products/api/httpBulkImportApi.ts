/**
 * Bulk Import — real backend implementation. Route paths follow the
 * existing supplier-discovery namespace, matching products/inventory's
 * own httpProductsApi.ts/httpInventoryApi.ts.
 *
 * SUBMIT IS multipart/form-data, NOT JSON -- the only place in this
 * whole app that uploads a file to TRU CONNECT'S OWN backend rather
 * than direct-to-Cloudinary (see cloudinaryUpload.ts's own docstring
 * on why product photos never go this route). Bulk import's images
 * arrive bundled inside one ZIP the supplier already has locally --
 * there's no per-image client-initiated signed upload step the way
 * single-product photos work, so the ZIP has to reach the backend
 * itself, which then uploads matched images to Cloudinary server-side
 * (see backend's own product_media_service.upload_and_register_from_bytes).
 *
 * 202 ACCEPTED, NOT A BLOCKING CALL -- the returned job is very likely
 * still UPLOADED by the time this resolves (the backend hands off to
 * its own background worker and returns immediately). Real progress
 * comes from POLLING getImportJob, never from this call's own
 * response.
 */
import { apiGet, apiPost } from "@/services/api/apiClient";

import type { ImportJob, ImportJobError, ImportJobStatus, ParsedImportFile } from "../types";
import type { PickedFile } from "../services/importSession";

interface ApiImportJob {
  id: string;
  status: ImportJobStatus;
  source_filename: string;
  has_images_zip: boolean;
  total_rows: number;
  valid_rows: number;
  error_rows: number;
  created_rows: number;
  images_total: number;
  images_matched: number;
  failure_reason: string | null;
  created_at: string;
  completed_at: string | null;
}

function fromApiImportJob(dto: ApiImportJob): ImportJob {
  return {
    id: dto.id,
    status: dto.status,
    sourceFilename: dto.source_filename,
    hasImagesZip: dto.has_images_zip,
    totalRows: dto.total_rows,
    validRows: dto.valid_rows,
    errorRows: dto.error_rows,
    createdRows: dto.created_rows,
    imagesTotal: dto.images_total,
    imagesMatched: dto.images_matched,
    failureReason: dto.failure_reason,
    createdAt: dto.created_at,
    completedAt: dto.completed_at,
  };
}

function mimeTypeFor(filename: string): string {
  const extension = filename.split(".").pop()?.toLowerCase();
  if (extension === "csv") return "text/csv";
  if (extension === "xlsx") return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
  if (extension === "zip") return "application/zip";
  return "application/octet-stream";
}

export async function submitImport(
  spreadsheetFile: PickedFile,
  zipFile: PickedFile | null,
  // Unused here -- the real backend re-parses/re-validates the actual
  // file independently and never trusts the client's own parse. Kept
  // in the signature only so this matches mockBulkImportApi.ts's own
  // signature exactly (mock mode has no server to parse against, so
  // it genuinely needs this).
  _parsedFile: ParsedImportFile
): Promise<ImportJob> {
  const formData = new FormData();
  // Same {uri, name, type} shape cloudinaryUpload.ts uses -- React
  // Native's networking layer streams the file at `uri` directly
  // rather than loading it into JS memory first.
  formData.append("spreadsheet", {
    uri: spreadsheetFile.uri,
    name: spreadsheetFile.name,
    type: mimeTypeFor(spreadsheetFile.name),
  } as unknown as Blob);

  if (zipFile) {
    formData.append("zip", {
      uri: zipFile.uri,
      name: zipFile.name,
      type: mimeTypeFor(zipFile.name),
    } as unknown as Blob);
  }

  // NO explicit Content-Type header here -- axios derives the correct
  // "multipart/form-data; boundary=..." header itself from the
  // FormData object. Setting Content-Type manually (a common mistake)
  // would override that with a boundary-less value, and Flask/
  // Werkzeug can't parse a multipart body without its boundary --
  // request.files would silently come back empty.
  const data = await apiPost<ApiImportJob>("/supplier-discovery/imports", formData);
  return fromApiImportJob(data);
}

export async function getImportJob(jobId: string): Promise<ImportJob> {
  const data = await apiGet<ApiImportJob>(`/supplier-discovery/imports/${jobId}`);
  return fromApiImportJob(data);
}

export async function getImportJobErrors(jobId: string): Promise<ImportJobError[]> {
  const data = await apiGet<{ results: { row_number: number; field: string; message: string }[] }>(
    `/supplier-discovery/imports/${jobId}/errors`
  );
  return data.results.map((e) => ({ rowNumber: e.row_number, field: e.field, message: e.message }));
}

export async function listImportJobs(): Promise<ImportJob[]> {
  const data = await apiGet<{ results: ApiImportJob[] }>("/supplier-discovery/imports");
  return data.results.map(fromApiImportJob);
}

/**
 * downloadDocuments.ts — the Import Template (XLSX) and Import Guide
 * (Word) are REAL, bundled files (assets/bulk-import/), not generated
 * on-device -- static content, so there's no reason to regenerate them
 * at runtime. Registered as bundleable assets via metro.config.js
 * (Metro's default assetExts doesn't include .xlsx/.docx).
 *
 * "Download" on a phone means the OS share sheet, not a literal
 * Downloads folder write -- neither iOS nor Android gives an app
 * direct write access to a user-visible folder without extra
 * permissions/setup, and the share sheet already lets the supplier
 * save to Files, send to email, open in Word/Excel, or AirDrop it,
 * which covers "I may need to modify it on my end" directly.
 */

import { Asset } from "expo-asset";
import * as Sharing from "expo-sharing";

const TEMPLATE_ASSET = require("../../../../../../assets/bulk-import/TRU_Connect_Product_Import_Template.xlsx");
const GUIDE_ASSET = require("../../../../../../assets/bulk-import/TRU_Connect_Bulk_Import_Guide.docx");

async function shareBundledAsset(moduleId: number, mimeType: string, dialogTitle: string): Promise<void> {
  const asset = Asset.fromModule(moduleId);
  await asset.downloadAsync();
  if (!asset.localUri) {
    throw new Error("Couldn't prepare the file for download.");
  }
  const canShare = await Sharing.isAvailableAsync();
  if (!canShare) {
    throw new Error("Sharing isn't available on this device.");
  }
  await Sharing.shareAsync(asset.localUri, { mimeType, dialogTitle });
}

export async function downloadImportTemplate(): Promise<void> {
  await shareBundledAsset(
    TEMPLATE_ASSET,
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "TruConnect Product Import Template"
  );
}

export async function downloadImportGuide(): Promise<void> {
  await shareBundledAsset(
    GUIDE_ASSET,
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "TruConnect Bulk Import Guide"
  );
}

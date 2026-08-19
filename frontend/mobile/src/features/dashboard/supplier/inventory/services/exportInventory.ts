/**
 * exportInventory.ts — mirrors products/services/exportProducts.ts
 * exactly (same base64/File/Sharing pattern), but the columns are
 * inventory's own: on hand, reserved, available, threshold, status --
 * the numbers a supplier actually opened this screen to check.
 */

import * as XLSX from "xlsx";
import { File, Paths } from "expo-file-system";
import * as Sharing from "expo-sharing";

import type { InventoryListItem } from "../types";
import { getInventoryList } from "../api/inventoryApi";
import { UNIT_OPTIONS } from "../../products/types";

function unitLabel(value: string): string {
  return UNIT_OPTIONS.find((o) => o.value === value)?.label ?? value;
}

function statusLabel(status: InventoryListItem["status"]): string {
  if (status === "IN_STOCK") return "In stock";
  if (status === "LOW_STOCK") return "Low stock";
  return "Out of stock";
}

function toExportRow(item: InventoryListItem): Record<string, string | number> {
  return {
    name: item.product.name,
    unit: unitLabel(item.product.sellingUnit),
    on_hand: item.inventory.quantityOnHand,
    reserved: item.inventory.quantityReserved,
    available: item.availableQuantity,
    low_stock_threshold: item.inventory.lowStockThreshold,
    status: statusLabel(item.status),
  };
}

function base64ToUint8Array(base64: string): Uint8Array {
  const binaryString = atob(base64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) bytes[i] = binaryString.charCodeAt(i);
  return bytes;
}

export async function exportInventory(): Promise<void> {
  const items = await getInventoryList({});

  const worksheet = XLSX.utils.json_to_sheet(items.map(toExportRow));
  worksheet["!cols"] = [
    { wch: 26 },
    { wch: 10 },
    { wch: 10 },
    { wch: 10 },
    { wch: 10 },
    { wch: 18 },
    { wch: 14 },
  ];

  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Inventory");

  const base64 = XLSX.write(workbook, { type: "base64", bookType: "xlsx" }) as string;
  const bytes = base64ToUint8Array(base64);

  const timestamp = new Date().toISOString().slice(0, 10);
  const file = new File(Paths.cache, `TRU_Connect_Inventory_${timestamp}.xlsx`);
  if (file.exists) file.delete();
  file.create();
  file.write(bytes);

  const canShare = await Sharing.isAvailableAsync();
  if (!canShare) {
    throw new Error("Sharing isn't available on this device.");
  }
  await Sharing.shareAsync(file.uri, {
    mimeType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    dialogTitle: "Export Inventory",
  });
}

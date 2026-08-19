/**
 * exportProducts.ts — the reverse of Import: generates a REAL XLSX
 * from the supplier's current catalogue, on-device, using the same
 * SheetJS (xlsx) library already installed for parsing imports.
 *
 * Columns mirror bulk-products' own importColumns.ts (name, category,
 * price, unit, stock) plus a leading `id` column carrying each
 * product's real internal id. That id column is FORWARD-LOOKING, NOT
 * YET CONSUMED BY THE IMPORT PARSER -- it's the mechanism the "update
 * via re-upload" idea (discussed alongside Import Products) depends
 * on: re-importing this exact export, once the parser recognises the
 * id column, updates existing products instead of creating duplicates.
 * Image columns are deliberately left BLANK in the export -- these are
 * existing products with existing images already attached; re-matching
 * them against a fresh ZIP isn't part of this flow (photo changes
 * happen on the product's own Edit screen).
 *
 * Always exports the FULL catalogue (ALL products, ignoring whatever
 * filter/search happens to be active on the list screen when the
 * supplier taps Export) -- the point of an export is a complete
 * backup/re-upload file, not whatever subset happens to be on screen.
 */

import * as XLSX from "xlsx";
import { File, Paths } from "expo-file-system";
import * as Sharing from "expo-sharing";

import type { Product } from "../types";
import { CATEGORY_OPTIONS, UNIT_OPTIONS } from "../types";
import { getProducts } from "../api/productsApi";

function labelFor<T extends string>(options: { value: T; label: string }[], value: T): string {
  return options.find((o) => o.value === value)?.label ?? value;
}

function toExportRow(product: Product): Record<string, string | number> {
  return {
    id: product.id,
    name: product.name,
    category: labelFor(CATEGORY_OPTIONS, product.category),
    price: (product.priceCents / 100).toFixed(2),
    unit: labelFor(UNIT_OPTIONS, product.sellingUnit),
    stock: product.stockStatus === "IN_STOCK" ? "In stock" : "Out of stock",
  };
}

function base64ToUint8Array(base64: string): Uint8Array {
  // atob, not Buffer -- same reasoning as this feature's own
  // useCurrentUserId.ts: Buffer is a Node.js global not guaranteed in
  // Hermes without a polyfill this project doesn't include.
  const binaryString = atob(base64);
  const bytes = new Uint8Array(binaryString.length);
  for (let i = 0; i < binaryString.length; i++) bytes[i] = binaryString.charCodeAt(i);
  return bytes;
}

export async function exportProducts(): Promise<void> {
  const products = await getProducts({});

  const worksheet = XLSX.utils.json_to_sheet(products.map(toExportRow));
  worksheet["!cols"] = [
    { wch: 24 }, // id
    { wch: 26 }, // name
    { wch: 22 }, // category
    { wch: 10 }, // price
    { wch: 12 }, // unit
    { wch: 14 }, // stock
  ];

  const workbook = XLSX.utils.book_new();
  XLSX.utils.book_append_sheet(workbook, worksheet, "Products");

  const base64 = XLSX.write(workbook, { type: "base64", bookType: "xlsx" }) as string;
  const bytes = base64ToUint8Array(base64);

  const timestamp = new Date().toISOString().slice(0, 10);
  const file = new File(Paths.cache, `TRU_Connect_Products_${timestamp}.xlsx`);
  if (file.exists) file.delete();
  file.create();
  file.write(bytes);

  const canShare = await Sharing.isAvailableAsync();
  if (!canShare) {
    throw new Error("Sharing isn't available on this device.");
  }
  await Sharing.shareAsync(file.uri, {
    mimeType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    dialogTitle: "Export Products",
  });
}

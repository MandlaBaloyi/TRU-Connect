/**
 * Reserved integration point for barcode/product-lookup providers.
 * Ref: master prompt "External API Ready > Barcode APIs (Future)" --
 * Product Lookup, Inventory, Catalogues.
 * Not implemented yet -- no current screen calls this.
 */
export async function lookupProductByBarcode(_barcode: string): Promise<never> {
  throw new Error(
    "barcodeIntegration.lookupProductByBarcode is not implemented yet -- see docs/08_PRODUCT_ROADMAP.txt"
  );
}

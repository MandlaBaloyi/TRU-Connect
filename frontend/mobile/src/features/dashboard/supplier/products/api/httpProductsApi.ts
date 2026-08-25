/**
 * Products — real backend implementation. Callable end-to-end as of
 * this pass: the backend's Product model matches this file's own
 * ApiProduct shape exactly (grown in Phase 1 of the backend build).
 *
 * Route paths follow the existing supplier-discovery namespace
 * (/api/v1/supplier-discovery/*), matching this codebase's real
 * routing.
 *
 * IMAGE UPLOAD IS ORCHESTRATED INSIDE createProduct, TRANSPARENT TO
 * THE CALLER -- AddProductScreen.tsx calls createProduct exactly once,
 * passing localImageUris, the same shape it's always called with in
 * mock mode. Internally here: create the product first (this is the
 * part that can genuinely fail the whole operation), THEN best-effort
 * sign+upload+register each local image ONE AT A TIME, catching
 * failures per-image rather than failing product creation over a
 * photo that didn't make it -- matches the exact "don't restart the
 * whole batch over one failed image" principle already proven out in
 * Bulk Import's own worker. A freshly uploaded image is PENDING, not
 * APPROVED, until Cloudinary's scan completes and the webhook fires --
 * so `images` on the RETURNED product is honestly still empty right
 * after creation even when every upload succeeded; that's expected,
 * not a bug (see docs/... the "Uploading... Scanning... Ready" UX this
 * was always designed around). Per-image retry UI is a natural,
 * separately-scoped follow-up, not built in this pass.
 */
import { apiDelete, apiGet, apiPatch, apiPost, ApiError } from "@/services/api/apiClient";

import type { CreateProductInput, Product, ProductFilters, UpdateProductInput } from "../types";
import type { PriceAdjustment } from "../../bulk-products/types";
import { ProductsError } from "../types";
import { uploadToCloudinary, type CloudinarySignedUpload } from "../services/cloudinaryUpload";

/**
 * Maps the backend's flat errors[] list (src/core/responses.py's own
 * envelope shape -- {success, message, data, errors, code}, never a
 * field-keyed object) back onto the specific form field each message
 * is actually about, so ProductForm's own fieldErrors.xxx display
 * (already built, already wired) has something real to show instead
 * of only ever the generic top-level message.
 *
 * REAL BUG FOUND DURING REVIEW: this mapping never existed at all --
 * every server-side validation error (a compare-at price that isn't
 * actually higher than the real price, a duplicate SKU, an
 * unrealistic price) has been showing ONLY the generic "Check the
 * highlighted fields" message since the day this screen shipped,
 * never red text under the actual field, even though the form has
 * been ready for it the whole time.
 *
 * KEYWORD MATCHING, NOT A STRUCTURAL FIX -- the real, fully robust
 * version would have the backend return {field, message} pairs
 * instead of plain strings, but that response shape
 * (src/core/responses.py's error_response) is shared across this
 * entire backend, not just Products -- changing it here would be a
 * breaking change to every other domain's error contract too, out of
 * scope for this one screen's fix. Order matters below: "compare-at
 * price" is checked BEFORE plain "price", since the compare-at
 * message itself contains the word "price" and would otherwise
 * wrongly attribute to the real price field.
 */
function mapErrorsToFields(errors: string[]): Record<string, string> {
  const fieldErrors: Record<string, string> = {};
  for (const message of errors) {
    const lower = message.toLowerCase();
    if (lower.includes("compare-at price") || lower.includes("compare at price")) {
      fieldErrors.compareAtPriceCents = message;
    } else if (lower.includes("sku")) {
      fieldErrors.sku = message;
    } else if (lower.includes("description")) {
      fieldErrors.description = message;
    } else if (lower.includes("price")) {
      fieldErrors.priceCents = message;
    } else if (lower.includes("category")) {
      fieldErrors.category = message;
    } else if (lower.includes("unit")) {
      fieldErrors.sellingUnit = message;
    } else if (lower.includes("name")) {
      fieldErrors.name = message;
    }
  }
  return fieldErrors;
}

interface ApiProduct {
  id: string;
  supplier_profile_id: string;
  name: string;
  category: string;
  price_cents: number;
  compare_at_price_cents: number | null;
  selling_unit: string;
  unit_quantity: number | null;
  unit_measure: string | null;
  description: string | null;
  sku: string;
  product_code: string;
  images: string[];
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

function fromApiProduct(dto: ApiProduct): Product {
  return {
    id: dto.id,
    supplierId: dto.supplier_profile_id,
    name: dto.name,
    category: dto.category as Product["category"],
    priceCents: dto.price_cents,
    compareAtPriceCents: dto.compare_at_price_cents,
    sellingUnit: dto.selling_unit as Product["sellingUnit"],
    unitQuantity: dto.unit_quantity,
    unitMeasure: dto.unit_measure as Product["unitMeasure"],
    description: dto.description,
    sku: dto.sku,
    productCode: dto.product_code,
    // LEGACY, backend no longer sends this field at all -- see
    // Product.stockStatus's own docstring (types.ts) for why it's kept
    // on the type but never read anywhere in this feature's UI
    // anymore. Defaulted rather than left undefined so nothing
    // downstream trips over a genuinely missing value for a field
    // TypeScript still thinks is required.
    stockStatus: "IN_STOCK",
    images: dto.images,
    isArchived: dto.is_archived,
    createdAt: dto.created_at,
    updatedAt: dto.updated_at,
  };
}

interface SignedUploadDto {
  cloud_name: string;
  api_key: string;
  timestamp: number;
  signature: string;
  public_id: string;
  upload_url: string;
  allowed_formats: string;
  transformation: string;
  notification_url: string;
  moderation: string;
  asset_folder: string;
}

async function requestUploadSignature(productId: string): Promise<CloudinarySignedUpload> {
  const data = await apiPost<SignedUploadDto>(
    `/supplier-discovery/products/${productId}/media/upload-signature`,
    {}
  );
  return {
    cloudName: data.cloud_name,
    apiKey: data.api_key,
    timestamp: data.timestamp,
    signature: data.signature,
    publicId: data.public_id,
    uploadUrl: data.upload_url,
    allowedFormats: data.allowed_formats,
    transformation: data.transformation,
    notificationUrl: data.notification_url,
    moderation: data.moderation,
    assetFolder: data.asset_folder,
  };
}

async function registerMedia(
  productId: string,
  uploaded: Awaited<ReturnType<typeof uploadToCloudinary>>
): Promise<void> {
  await apiPost(`/supplier-discovery/products/${productId}/media`, {
    cloudinary_public_id: uploaded.publicId,
    secure_url: uploaded.secureUrl,
    resource_type: uploaded.resourceType,
    format: uploaded.format,
    width: uploaded.width,
    height: uploaded.height,
    bytes: uploaded.bytes,
  });
}

/**
 * Best-effort, one image at a time, in order (position 0 = cover,
 * matching Product.images' own convention -- uploading in order means
 * the FIRST successfully-approved image stays the cover once scanning
 * completes, without this function needing to track sort_order itself;
 * the backend already assigns it by upload order). A single image
 * failing (network drop, oversized file, tier limit) is logged and
 * skipped, never thrown -- see this file's own header docstring for
 * why product creation must not fail over a photo.
 */
async function uploadProductImagesBestEffort(productId: string, localUris: string[]): Promise<void> {
  for (const localUri of localUris) {
    try {
      const signed = await requestUploadSignature(productId);
      const uploaded = await uploadToCloudinary(signed, localUri);
      await registerMedia(productId, uploaded);
    } catch (error) {
      // eslint-disable-next-line no-console
      console.warn("Product photo upload failed, continuing with the rest:", error);
    }
  }
}

export async function getProducts(filters: ProductFilters = {}): Promise<Product[]> {
  const data = await apiGet<{ results: ApiProduct[] }>("/supplier-discovery/products", {
    params: {
      q: filters.searchTerm || undefined,
      filter: filters.listFilter,
    },
  });
  return data.results.map(fromApiProduct);
}

export async function getProduct(id: string): Promise<Product> {
  try {
    const data = await apiGet<ApiProduct>(`/supplier-discovery/products/${id}`);
    return fromApiProduct(data);
  } catch (error) {
    if (error instanceof ApiError && error.code === "PRODUCT_NOT_FOUND") {
      throw new ProductsError("Product not found.", "PRODUCT_NOT_FOUND");
    }
    throw error;
  }
}

export async function createProduct(input: CreateProductInput): Promise<Product> {
  let product: Product;
  try {
    const data = await apiPost<ApiProduct>("/supplier-discovery/products", {
      name: input.name.trim(),
      category: input.category,
      price_cents: input.priceCents,
      selling_unit: input.sellingUnit,
      // stock_status is NOT sent -- Inventory owns stock status now
      // (see products/types.ts's own Product.stockStatus docstring);
      // the real backend seeds an Inventory record separately,
      // matching AddProductScreen's own two-call sequence.
      // undefined (never sent) means "leave it blank" for sku --
      // the backend auto-generates one. Never product_code -- that
      // field doesn't exist in this request at all, matching the
      // backend's own schema, which never declares it either.
      sku: input.sku,
      description: input.description,
      compare_at_price_cents: input.compareAtPriceCents,
    });
    product = fromApiProduct(data);
  } catch (error) {
    if (error instanceof ApiError && error.code === "VALIDATION_ERROR") {
      throw new ProductsError(error.message, "VALIDATION_ERROR", mapErrorsToFields(error.errors));
    }
    throw error;
  }

  if (input.localImageUris.length > 0) {
    await uploadProductImagesBestEffort(product.id, input.localImageUris);
  }

  return product;
}

export async function archiveProduct(id: string): Promise<Product> {
  try {
    const data = await apiPost<ApiProduct>(`/supplier-discovery/products/${id}/archive`, {});
    return fromApiProduct(data);
  } catch (error) {
    if (error instanceof ApiError && error.code === "PRODUCT_NOT_FOUND") {
      throw new ProductsError("Product not found.", "PRODUCT_NOT_FOUND");
    }
    throw error;
  }
}

export async function unarchiveProduct(id: string): Promise<Product> {
  try {
    const data = await apiPost<ApiProduct>(`/supplier-discovery/products/${id}/unarchive`, {});
    return fromApiProduct(data);
  } catch (error) {
    if (error instanceof ApiError && error.code === "PRODUCT_NOT_FOUND") {
      throw new ProductsError("Product not found.", "PRODUCT_NOT_FOUND");
    }
    throw error;
  }
}

export async function deleteProduct(id: string): Promise<void> {
  try {
    await apiDelete(`/supplier-discovery/products/${id}`);
  } catch (error) {
    if (error instanceof ApiError && error.code === "PRODUCT_NOT_FOUND") {
      throw new ProductsError("Product not found.", "PRODUCT_NOT_FOUND");
    }
    throw error;
  }
}

export async function updateProduct(input: UpdateProductInput): Promise<Product> {
  try {
    const data = await apiPatch<ApiProduct>(`/supplier-discovery/products/${input.id}`, {
      name: input.name.trim(),
      category: input.category,
      price_cents: input.priceCents,
      selling_unit: input.sellingUnit,
      // stock_status intentionally not sent -- Edit Product no longer
      // touches it, same reasoning as createProduct above.
      // Edit Product's own image upload (attaching NEW photos to an
      // already-existing product, distinct from images already
      // approved) is a separately-scoped follow-up -- this call
      // updates the text fields only; ProductForm's own images array
      // for an edit is a mix of already-remote URLs (nothing to do)
      // and potentially-new local URIs (not yet wired to upload here).
      // undefined sku means "leave the existing one alone" -- matches
      // the backend's own update_product semantics exactly. Still
      // never product_code, same reasoning as createProduct above.
      sku: input.sku,
      description: input.description,
      compare_at_price_cents: input.compareAtPriceCents,
    });
    return fromApiProduct(data);
  } catch (error) {
    if (error instanceof ApiError && error.code === "VALIDATION_ERROR") {
      throw new ProductsError(error.message, "VALIDATION_ERROR", mapErrorsToFields(error.errors));
    }
    if (error instanceof ApiError && error.code === "PRODUCT_NOT_FOUND") {
      throw new ProductsError("Product not found.", "PRODUCT_NOT_FOUND");
    }
    throw error;
  }
}

// ---------------------------------------------------------------------------
// Bulk actions -- each is ONE request carrying every selected id, not N
// sequential requests. This matters beyond just being tidy: N requests
// for a 200-product selection is 200 round trips, 200 chances to
// partially fail, and no way to report "197 succeeded, 3 didn't" as a
// single coherent result -- exactly the kind of thing this feature's
// own bulk-import security/architecture discussion was about avoiding.
// ---------------------------------------------------------------------------

export async function bulkAdjustPrice(productIds: string[], adjustment: PriceAdjustment): Promise<Product[]> {
  const data = await apiPost<{ results: ApiProduct[] }>("/supplier-discovery/products/bulk/adjust-price", {
    product_ids: productIds,
    direction: adjustment.direction,
    // REAL BUG FOUND DURING DEVICE TESTING: this used to be sent as
    // "adjustment_type". The backend's own BulkAdjustPriceSchema
    // requires a field literally named "type" (required=True) --
    // sending "adjustment_type" instead meant the required field was
    // simply never present, and the backend correctly rejected every
    // request with a 422. Same class of bug as the PUT/PATCH mismatch
    // on Edit Product, just a JSON key instead of an HTTP verb.
    type: adjustment.type,
    value: adjustment.value,
  });
  return data.results.map(fromApiProduct);
}

export async function bulkSetDiscount(productIds: string[], discountPercent: number): Promise<Product[]> {
  const data = await apiPost<{ results: ApiProduct[] }>("/supplier-discovery/products/bulk/discount", {
    product_ids: productIds,
    discount_percent: discountPercent,
  });
  return data.results.map(fromApiProduct);
}

export async function bulkArchiveProducts(productIds: string[]): Promise<Product[]> {
  const data = await apiPost<{ results: ApiProduct[] }>("/supplier-discovery/products/bulk/archive", {
    product_ids: productIds,
  });
  return data.results.map(fromApiProduct);
}

export async function bulkUnarchiveProducts(productIds: string[]): Promise<Product[]> {
  const data = await apiPost<{ results: ApiProduct[] }>("/supplier-discovery/products/bulk/unarchive", {
    product_ids: productIds,
  });
  return data.results.map(fromApiProduct);
}

export async function bulkDeleteProducts(productIds: string[]): Promise<void> {
  await apiPost("/supplier-discovery/products/bulk/delete", { product_ids: productIds });
}

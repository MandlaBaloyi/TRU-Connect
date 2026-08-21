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
import { apiGet, apiPost, apiPut, ApiError } from "@/services/api/apiClient";

import type { CreateProductInput, Product, ProductFilters, UpdateProductInput } from "../types";
import type { PriceAdjustment } from "../../bulk-products/types";
import { ProductsError } from "../types";
import { uploadToCloudinary, type CloudinarySignedUpload } from "../services/cloudinaryUpload";

interface ApiProduct {
  id: string;
  supplier_profile_id: string;
  name: string;
  category: string;
  price_cents: number;
  selling_unit: string;
  unit_quantity: number | null;
  unit_measure: string | null;
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
    sellingUnit: dto.selling_unit as Product["sellingUnit"],
    unitQuantity: dto.unit_quantity,
    unitMeasure: dto.unit_measure as Product["unitMeasure"],
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
    });
    product = fromApiProduct(data);
  } catch (error) {
    if (error instanceof ApiError && error.code === "VALIDATION_ERROR") {
      // Per-field mapping isn't defined yet -- the real envelope
      // ({success, message, data, errors, code}, src/core/responses.py)
      // carries a flat errors[] list, not a field-keyed object.
      throw new ProductsError(error.message, "VALIDATION_ERROR");
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

export async function updateProduct(input: UpdateProductInput): Promise<Product> {
  try {
    const data = await apiPut<ApiProduct>(`/supplier-discovery/products/${input.id}`, {
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
    });
    return fromApiProduct(data);
  } catch (error) {
    if (error instanceof ApiError && error.code === "VALIDATION_ERROR") {
      throw new ProductsError(error.message, "VALIDATION_ERROR");
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
    adjustment_type: adjustment.type,
    value: adjustment.value,
  });
  return data.results.map(fromApiProduct);
}

export async function bulkArchiveProducts(productIds: string[]): Promise<Product[]> {
  const data = await apiPost<{ results: ApiProduct[] }>("/supplier-discovery/products/bulk/archive", {
    product_ids: productIds,
  });
  return data.results.map(fromApiProduct);
}

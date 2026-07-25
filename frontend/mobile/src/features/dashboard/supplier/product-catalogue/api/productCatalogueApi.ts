import { apiClient } from '@/services/api/apiClient';
import { USE_MOCK_API } from '@/constants/config';
import type {
  Product,
  ProductImage,
  ProductFilters,
  PaginatedProducts,
  CreateProductInput,
  UpdateProductInput,
  StockStatus,
} from '../types';
import { fromApiProduct, toApiCreatePayload, toApiUpdatePayload } from '../services/productMapper';

/**
 * Product Catalogue API layer.
 *
 * Endpoints mirror Document 05 \u00a75.3 exactly:
 *   GET    /products                    list/search (filters: category,
 *                                        supplier_id, keyword, price range)
 *   GET    /products/{id}               product detail
 *   POST   /products                    create (supplier only)
 *   PUT    /products/{id}               update (supplier only, own product)
 *   DELETE /products/{id}               soft-delete/unpublish
 *   PUT    /products/{id}/availability  toggle stock_status
 *   POST   /products/{id}/images        add image
 *   DELETE /products/{id}/images/{id}   remove image
 *
 * Uses the app-wide USE_MOCK_API flag (src/constants/config.ts) since the
 * Flask backend is still under development -- this stays in sync with
 * every other feature's mock/real switch instead of maintaining its own.
 */
const MOCK_LATENCY_MS = 350;
const MOCK_SUPPLIER_ID = 'mock-supplier-001';

function wait<T>(value: T, ms = MOCK_LATENCY_MS): Promise<T> {
  return new Promise((resolve) => setTimeout(() => resolve(value), ms));
}

function generateId(prefix: string): string {
  return `${prefix}-${Math.random().toString(36).slice(2, 10)}-${Date.now().toString(36)}`;
}

function nowIso(): string {
  return new Date().toISOString();
}

let mockProducts: Product[] = [
  {
    id: 'prod-0001',
    supplierId: MOCK_SUPPLIER_ID,
    categoryId: 'cat-beverages',
    categoryName: 'Beverages',
    name: 'Sparkling Water 500ml (Case of 24)',
    description:
      'Case of 24 x 500ml sparkling water bottles, ideal for restaurants and retailers.',
    price: 189.99,
    unit: 'case',
    bulkPricingRules: [
      { id: 'tier-0001', minQuantity: 10, price: 175 },
      { id: 'tier-0002', minQuantity: 25, price: 159.99 },
    ],
    minimumOrderQuantity: 2,
    stockStatus: 'in_stock',
    isPublished: true,
    images: [
      {
        id: 'img-0001',
        productId: 'prod-0001',
        imageUrl: 'https://picsum.photos/seed/prod0001/600/600',
        sortOrder: 0,
      },
    ],
    createdAt: nowIso(),
    updatedAt: nowIso(),
  },
  {
    id: 'prod-0002',
    supplierId: MOCK_SUPPLIER_ID,
    categoryId: 'cat-cleaning',
    categoryName: 'Cleaning Supplies',
    name: 'Industrial Floor Cleaner 5L',
    description: 'Concentrated industrial-strength floor cleaner, 5 litre container.',
    price: 249.5,
    unit: 'each',
    bulkPricingRules: [],
    minimumOrderQuantity: 1,
    stockStatus: 'low_stock',
    isPublished: true,
    images: [],
    createdAt: nowIso(),
    updatedAt: nowIso(),
  },
  {
    id: 'prod-0003',
    supplierId: MOCK_SUPPLIER_ID,
    categoryId: 'cat-packaging',
    categoryName: 'Packaging',
    name: 'Branded Takeaway Boxes (Pack of 100)',
    description: 'Draft listing -- pending final pricing confirmation.',
    price: 0,
    unit: 'pack',
    bulkPricingRules: [],
    minimumOrderQuantity: 1,
    stockStatus: 'in_stock',
    isPublished: false,
    images: [],
    createdAt: nowIso(),
    updatedAt: nowIso(),
  },
];

function applyFilters(products: Product[], filters: ProductFilters): Product[] {
  return products.filter((product) => {
    if (filters.categoryId && product.categoryId !== filters.categoryId) return false;
    if (filters.stockStatus && product.stockStatus !== filters.stockStatus) return false;
    if (filters.publishedOnly && !product.isPublished) return false;
    if (filters.keyword) {
      const q = filters.keyword.toLowerCase();
      if (
        !product.name.toLowerCase().includes(q) &&
        !product.description.toLowerCase().includes(q)
      ) {
        return false;
      }
    }
    return true;
  });
}

export const productCatalogueApi = {
  async list(filters: ProductFilters = {}): Promise<PaginatedProducts> {
    const page = filters.page ?? 1;
    const pageSize = filters.pageSize ?? 20;

    if (USE_MOCK_API) {
      const filtered = applyFilters(mockProducts, filters);
      const start = (page - 1) * pageSize;
      return wait({
        products: filtered.slice(start, start + pageSize),
        total: filtered.length,
        page,
        pageSize,
      });
    }

    const { data } = await apiClient.get('/products', {
      params: {
        keyword: filters.keyword,
        category_id: filters.categoryId,
        stock_status: filters.stockStatus,
        published_only: filters.publishedOnly,
        page,
        page_size: pageSize,
      },
    });
    return {
      products: data.results.map(fromApiProduct),
      total: data.total,
      page: data.page,
      pageSize: data.page_size,
    };
  },

  async getById(id: string): Promise<Product> {
    if (USE_MOCK_API) {
      const found = mockProducts.find((product) => product.id === id);
      if (!found) throw new Error('Product not found');
      return wait(found);
    }
    const { data } = await apiClient.get(`/products/${id}`);
    return fromApiProduct(data);
  },

  async create(input: CreateProductInput): Promise<Product> {
    if (USE_MOCK_API) {
      const product: Product = {
        id: generateId('prod'),
        supplierId: MOCK_SUPPLIER_ID,
        categoryId: input.categoryId,
        categoryName: '',
        name: input.name,
        description: input.description,
        price: input.price,
        unit: input.unit,
        bulkPricingRules: (input.bulkPricingRules ?? []).map((tier) => ({
          ...tier,
          id: generateId('tier'),
        })),
        minimumOrderQuantity: input.minimumOrderQuantity,
        stockStatus: input.stockStatus,
        isPublished: input.isPublished,
        images: [],
        createdAt: nowIso(),
        updatedAt: nowIso(),
      };
      mockProducts = [product, ...mockProducts];
      return wait(product);
    }
    const { data } = await apiClient.post('/products', toApiCreatePayload(input));
    return fromApiProduct(data);
  },

  async update(id: string, input: UpdateProductInput): Promise<Product> {
    if (USE_MOCK_API) {
      const index = mockProducts.findIndex((product) => product.id === id);
      if (index === -1) throw new Error('Product not found');
      const updated: Product = {
        ...mockProducts[index],
        ...input,
        bulkPricingRules: input.bulkPricingRules
          ? input.bulkPricingRules.map((tier) => ({ ...tier, id: generateId('tier') }))
          : mockProducts[index].bulkPricingRules,
        updatedAt: nowIso(),
      };
      mockProducts[index] = updated;
      return wait(updated);
    }
    const { data } = await apiClient.put(`/products/${id}`, toApiUpdatePayload(input));
    return fromApiProduct(data);
  },

  /** Document 06 \u00a74: deleting a product soft-deletes / unpublishes it. */
  async remove(id: string): Promise<void> {
    if (USE_MOCK_API) {
      const index = mockProducts.findIndex((product) => product.id === id);
      if (index === -1) throw new Error('Product not found');
      mockProducts[index] = { ...mockProducts[index], isPublished: false, updatedAt: nowIso() };
      return wait(undefined);
    }
    await apiClient.delete(`/products/${id}`);
  },

  async setAvailability(id: string, stockStatus: StockStatus): Promise<Product> {
    return productCatalogueApi.update(id, { stockStatus });
  },

  async addImage(productId: string, imageUrl: string): Promise<ProductImage> {
    if (USE_MOCK_API) {
      const index = mockProducts.findIndex((product) => product.id === productId);
      if (index === -1) throw new Error('Product not found');
      const image: ProductImage = {
        id: generateId('img'),
        productId,
        imageUrl,
        sortOrder: mockProducts[index].images.length,
      };
      mockProducts[index] = {
        ...mockProducts[index],
        images: [...mockProducts[index].images, image],
        updatedAt: nowIso(),
      };
      return wait(image);
    }
    const { data } = await apiClient.post(`/products/${productId}/images`, { image_url: imageUrl });
    return { id: data.id, productId, imageUrl: data.image_url, sortOrder: data.sort_order };
  },

  async removeImage(productId: string, imageId: string): Promise<void> {
    if (USE_MOCK_API) {
      const index = mockProducts.findIndex((product) => product.id === productId);
      if (index === -1) throw new Error('Product not found');
      mockProducts[index] = {
        ...mockProducts[index],
        images: mockProducts[index].images.filter((image) => image.id !== imageId),
        updatedAt: nowIso(),
      };
      return wait(undefined);
    }
    await apiClient.delete(`/products/${productId}/images/${imageId}`);
  },
};

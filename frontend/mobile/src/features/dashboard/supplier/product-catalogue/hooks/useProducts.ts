import { useQuery } from '@tanstack/react-query';
import { productCatalogueApi } from '../api/productCatalogueApi';
import type { ProductFilters } from '../types';

export const productCatalogueQueryKeys = {
  all: ['product-catalogue'] as const,
  lists: () => [...productCatalogueQueryKeys.all, 'list'] as const,
  list: (filters: ProductFilters) => [...productCatalogueQueryKeys.lists(), filters] as const,
  details: () => [...productCatalogueQueryKeys.all, 'detail'] as const,
  detail: (id: string) => [...productCatalogueQueryKeys.details(), id] as const,
};

export function useProducts(filters: ProductFilters = {}) {
  return useQuery({
    queryKey: productCatalogueQueryKeys.list(filters),
    queryFn: () => productCatalogueApi.list(filters),
    placeholderData: (previous) => previous,
  });
}

export function useProduct(id: string | undefined) {
  return useQuery({
    queryKey: productCatalogueQueryKeys.detail(id ?? ''),
    queryFn: () => productCatalogueApi.getById(id as string),
    enabled: Boolean(id),
  });
}

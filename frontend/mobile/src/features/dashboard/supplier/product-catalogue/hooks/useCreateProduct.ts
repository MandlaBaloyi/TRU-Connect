import { useMutation, useQueryClient } from '@tanstack/react-query';
import { productCatalogueApi } from '../api/productCatalogueApi';
import { productCatalogueQueryKeys } from './useProducts';
import type { CreateProductInput } from '../types';

export function useCreateProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (input: CreateProductInput) => productCatalogueApi.create(input),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: productCatalogueQueryKeys.lists() });
    },
  });
}

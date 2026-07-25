import { useMutation, useQueryClient } from '@tanstack/react-query';
import { productCatalogueApi } from '../api/productCatalogueApi';
import { productCatalogueQueryKeys } from './useProducts';
import type { UpdateProductInput } from '../types';

interface UpdateProductArgs {
  id: string;
  input: UpdateProductInput;
}

export function useUpdateProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: UpdateProductArgs) => productCatalogueApi.update(id, input),
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({ queryKey: productCatalogueQueryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: productCatalogueQueryKeys.detail(variables.id) });
    },
  });
}

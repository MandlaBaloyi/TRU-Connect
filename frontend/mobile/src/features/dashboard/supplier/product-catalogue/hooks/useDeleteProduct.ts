import { useMutation, useQueryClient } from '@tanstack/react-query';
import { productCatalogueApi } from '../api/productCatalogueApi';
import { productCatalogueQueryKeys } from './useProducts';

/** Document 06 \u00a74: this soft-deletes / unpublishes rather than hard-deleting. */
export function useDeleteProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => productCatalogueApi.remove(id),
    onSuccess: (_data, id) => {
      queryClient.invalidateQueries({ queryKey: productCatalogueQueryKeys.lists() });
      queryClient.invalidateQueries({ queryKey: productCatalogueQueryKeys.detail(id) });
    },
  });
}

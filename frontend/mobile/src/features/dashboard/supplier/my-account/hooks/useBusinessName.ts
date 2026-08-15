import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { getMyBusinessName, updateMyBusinessName } from "../services/accountService";

const businessNameKey = ["supplierMyAccount", "businessName"] as const;

export function useSupplierBusinessName() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: businessNameKey,
    queryFn: getMyBusinessName,
  });

  const mutation = useMutation({
    mutationFn: (value: string) => updateMyBusinessName(value),
    onSuccess: (saved) => queryClient.setQueryData(businessNameKey, saved),
  });

  return {
    businessName: query.data ?? null,
    isLoading: query.isLoading,
    save: mutation.mutateAsync,
    isSaving: mutation.isPending,
  };
}

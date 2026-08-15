import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  approveRequest,
  declineRequest,
  getSupplierRequestDetail,
} from "../services/supplierRequestsService";
import type { SupplierRequestDetail } from "../types";

const detailKey = (id: string) => ["supplierRequests", "detail", id] as const;

export function useSupplierRequestDetail(id: string) {
  return useQuery({
    queryKey: detailKey(id),
    queryFn: () => getSupplierRequestDetail(id),
    enabled: Boolean(id),
  });
}

export function useRespondToRequest(id: string) {
  const queryClient = useQueryClient();

  const invalidateList = () => queryClient.invalidateQueries({ queryKey: ["supplierRequests", "list"] });

  const approve = useMutation({
    mutationFn: () => approveRequest(id),
    onSuccess: (status) => {
      queryClient.setQueryData<SupplierRequestDetail | null>(detailKey(id), (current) =>
        current ? { ...current, status } : current
      );
      invalidateList();
    },
  });

  const decline = useMutation({
    mutationFn: () => declineRequest(id),
    onSuccess: (status) => {
      queryClient.setQueryData<SupplierRequestDetail | null>(detailKey(id), (current) =>
        current ? { ...current, status } : current
      );
      invalidateList();
    },
  });

  return {
    approve: approve.mutateAsync,
    isApproving: approve.isPending,
    decline: decline.mutateAsync,
    isDeclining: decline.isPending,
  };
}

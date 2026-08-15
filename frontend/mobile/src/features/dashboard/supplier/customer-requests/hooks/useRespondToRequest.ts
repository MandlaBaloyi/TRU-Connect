import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import {
  approveRequest,
  declineRequest,
  getCustomerRequestDetail,
} from "../services/customerRequestsService";
import type { CustomerRequestDetail } from "../types";

const detailKey = (id: string) => ["customerRequests", "detail", id] as const;

export function useCustomerRequestDetail(id: string) {
  return useQuery({
    queryKey: detailKey(id),
    queryFn: () => getCustomerRequestDetail(id),
    enabled: Boolean(id),
  });
}

export function useRespondToRequest(id: string) {
  const queryClient = useQueryClient();

  const invalidateList = () => queryClient.invalidateQueries({ queryKey: ["customerRequests", "list"] });

  const approve = useMutation({
    mutationFn: () => approveRequest(id),
    onSuccess: (status) => {
      queryClient.setQueryData<CustomerRequestDetail | null>(detailKey(id), (current) =>
        current ? { ...current, status } : current
      );
      invalidateList();
    },
  });

  const decline = useMutation({
    mutationFn: () => declineRequest(id),
    onSuccess: (status) => {
      queryClient.setQueryData<CustomerRequestDetail | null>(detailKey(id), (current) =>
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

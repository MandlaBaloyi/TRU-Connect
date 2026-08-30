import { useMutation } from "@tanstack/react-query";

import { reportSupplier } from "../services/supplierSearchService";
import type { ReportReason } from "../types";

export function useReportSupplier(supplierId: string) {
  const mutation = useMutation({
    mutationFn: ({ reason, details, productId }: { reason: ReportReason; details: string | null; productId?: string }) =>
      reportSupplier(supplierId, reason, details, productId),
  });

  return {
    reportSupplier: mutation.mutateAsync,
    isReporting: mutation.isPending,
  };
}

/**
 * useLoanPayments — every Loan Book write.
 *
 * OPTIMISTIC UPDATES on payment recording are not polish, they are the
 * requirement: "Record Payment ≤ 15 seconds". A shop owner standing at a
 * counter cannot wait for I/O before the screen acknowledges them. The
 * balance updates immediately and rolls back if the write fails —
 * because the owner must never be left believing a payment was recorded
 * when it was not (Doc 02 §12.3 applies the same principle to orders).
 */

import { useMutation, useQueryClient } from "@tanstack/react-query";

import type { LoanEntryView, RecordCreditSaleInput, RecordPaymentInput } from "../types";
import {
  deleteLoanEntry,
  restoreLoanEntry,
  deletePayment,
  recordCreditSale,
  recordPayment,
} from "../api/loanBookApi";
import { loanBookKeys } from "./loanBookKeys";

export function useLoanPayments() {
  const queryClient = useQueryClient();

  // Invalidate the whole feature after any write. Narrower invalidation
  // would be marginally faster and would eventually leave one screen
  // showing a balance that contradicts another — precisely the
  // inconsistency the derived-balance rule exists to prevent.
  const invalidateAll = () => {
    queryClient.invalidateQueries({ queryKey: loanBookKeys.all });
  };

  const recordPaymentMutation = useMutation({
    mutationFn: (input: RecordPaymentInput) => recordPayment(input),

    onMutate: async (input) => {
      await queryClient.cancelQueries({ queryKey: loanBookKeys.entry(input.loanEntryId) });
      const previous = queryClient.getQueryData<LoanEntryView | null>(
        loanBookKeys.entry(input.loanEntryId)
      );

      if (previous) {
        const optimisticOutstanding = Math.max(0, previous.outstandingAmount - input.amount);
        queryClient.setQueryData<LoanEntryView>(loanBookKeys.entry(input.loanEntryId), {
          ...previous,
          outstandingAmount: optimisticOutstanding,
          amountPaid: previous.amountPaid + input.amount,
          status: optimisticOutstanding === 0 ? "PAID" : previous.status,
        });
      }

      return { previous };
    },

    onError: (_error, input, context) => {
      if (context?.previous) {
        queryClient.setQueryData(loanBookKeys.entry(input.loanEntryId), context.previous);
      }
    },

    onSettled: invalidateAll,
  });

  const recordSaleMutation = useMutation({
    mutationFn: (input: RecordCreditSaleInput) => recordCreditSale(input),
    onSuccess: invalidateAll,
  });

  const deleteEntryMutation = useMutation({
    mutationFn: ({ entryId, reason }: { entryId: string; reason?: string }) =>
      deleteLoanEntry(entryId, reason),
    onSuccess: invalidateAll,
  });

  const restoreEntryMutation = useMutation({
    mutationFn: (entryId: string) => restoreLoanEntry(entryId),
    onSuccess: invalidateAll,
  });

  const deletePaymentMutation = useMutation({
    mutationFn: ({ paymentId, entryId }: { paymentId: string; entryId: string }) =>
      deletePayment(paymentId, entryId),
    onSuccess: invalidateAll,
  });

  return {
    recordPayment: recordPaymentMutation.mutateAsync,
    isRecordingPayment: recordPaymentMutation.isPending,
    recordPaymentError: recordPaymentMutation.error,

    recordSale: recordSaleMutation.mutateAsync,
    isRecordingSale: recordSaleMutation.isPending,
    recordSaleError: recordSaleMutation.error,

    deleteEntry: deleteEntryMutation.mutateAsync,
    isDeletingEntry: deleteEntryMutation.isPending,

    restoreEntry: restoreEntryMutation.mutateAsync,
    isRestoringEntry: restoreEntryMutation.isPending,

    deletePayment: deletePaymentMutation.mutateAsync,
    isDeletingPayment: deletePaymentMutation.isPending,
  };
}

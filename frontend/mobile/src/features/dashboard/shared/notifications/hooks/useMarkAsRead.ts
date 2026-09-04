import { useMutation, useQueryClient } from "@tanstack/react-query";

import * as notificationsService from "../services/notificationsService";

export function useMarkAsRead() {
  const queryClient = useQueryClient();

  const single = useMutation({
    mutationFn: (notificationId: string) => notificationsService.markAsRead(notificationId),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  const all = useMutation({
    mutationFn: () => notificationsService.markAllAsRead(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["notifications"] });
    },
  });

  return {
    markAsRead: single.mutateAsync,
    markAllAsRead: all.mutateAsync,
    isMarkingAll: all.isPending,
  };
}

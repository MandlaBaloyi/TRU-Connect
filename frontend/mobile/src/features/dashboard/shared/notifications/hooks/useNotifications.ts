import { useQuery, useQueryClient } from "@tanstack/react-query";

import * as notificationsService from "../services/notificationsService";
import type { NotificationCategory } from "../types";

export function useNotifications(category?: NotificationCategory) {
  const queryClient = useQueryClient();
  const queryKey = ["notifications", "list", category ?? "ALL"];

  const query = useQuery({
    queryKey,
    queryFn: () => notificationsService.getNotifications(category),
    // THE REAL FIX for a genuine, confirmed report: this project's own
    // global queryClient.ts sets a 30s staleTime everywhere by
    // default -- fine for most data, but actively misleading here.
    // Without this override, opening the Inbox tab within 30s of a
    // prior visit served the CACHED, pre-request list, while the
    // header's own unread badge (useUnreadCount, its own independent
    // 30s poll) could catch up on a different schedule -- exactly
    // the "only sending to the home tab" pattern reported directly.
    // staleTime: 0 means every mount/focus genuinely refetches.
    staleTime: 0,
  });

  return {
    notifications: query.data ?? [],
    isLoading: query.isLoading,
    isError: query.isError,
    refetch: query.refetch,
    isRefetching: query.isRefetching,
  };
}

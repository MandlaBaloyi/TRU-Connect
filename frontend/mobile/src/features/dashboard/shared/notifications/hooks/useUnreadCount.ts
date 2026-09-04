import { useQuery } from "@tanstack/react-query";

import * as notificationsService from "../services/notificationsService";

/** Feeds the bell icon's own badge -- the ONE thing a screen far away
 *  from this whole feature (DashboardHeader) actually needs, without
 *  ever knowing categories, response shapes, or anything else about
 *  how notifications work underneath.
 *
 *  Polls every 30s -- an honest, pragmatic middle ground: there's no
 *  real push infrastructure yet (see this feature's own planning
 *  notes), so the badge won't update the INSTANT a new notification
 *  arrives, but it also won't go stale for the length of a whole app
 *  session either. */
export function useUnreadCount() {
  const query = useQuery({
    queryKey: ["notifications", "unread-count"],
    queryFn: () => notificationsService.getUnreadCount(),
    refetchInterval: 30_000,
    // Same reasoning as useNotifications' own staleTime: 0 -- this
    // project's global 30s staleTime could otherwise delay even the
    // INITIAL mount's own fetch, relying solely on the interval timer
    // to eventually catch up.
    staleTime: 0,
  });

  return { count: query.data ?? 0 };
}

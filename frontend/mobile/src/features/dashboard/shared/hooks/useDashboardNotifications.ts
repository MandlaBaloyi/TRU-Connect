
/**** 
import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/services/api/apiClient";

export interface DashboardNotification {
  id: string;
  notificationType: string;
  title: string;
  body: string;
  isRead: boolean;
  createdAt: string;
}


 * Shared notification-fetching hook -- both dashboards show the same
 * notification bell + badge (DashboardHeader), so this hook is genuinely
 * cross-cutting rather than business- or supplier-specific.
 * Ref: docs/05_BACKEND_API_SPECIFICATION.txt, Section 5.7 (Platform
 * Domain: GET /notifications, GET /notifications/unread-count).
 
export function useDashboardNotifications() {
  return useQuery({
    queryKey: ["dashboard-notifications"],
    queryFn: async (): Promise<DashboardNotification[]> => {
      const { data } = await apiClient.get("/notifications");
      return data.items ?? data;
    },
  });
}

export function useUnreadNotificationCount() {
  return useQuery({
    queryKey: ["dashboard-notifications", "unread-count"],
    queryFn: async (): Promise<number> => {
      const { data } = await apiClient.get("/notifications/unread-count");
      return data.count ?? 0;
    },
  });
}
****/

import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/services/api/apiClient";
import { USE_MOCK_API } from "@/constants/config";
import { mockDelay, MOCK_NOTIFICATIONS, MOCK_UNREAD_COUNT } from "@/services/api/mockData";

export interface DashboardNotification {
  id: string;
  notificationType: string;
  title: string;
  body: string;
  isRead: boolean;
  createdAt: string;
}

export function useDashboardNotifications() {
  return useQuery({
    queryKey: ["dashboard-notifications"],
    queryFn: async (): Promise<DashboardNotification[]> => {
      if (USE_MOCK_API) return mockDelay(MOCK_NOTIFICATIONS);
      const { data } = await apiClient.get("/notifications");
      return data.items ?? data;
    },
  });
}

export function useUnreadNotificationCount() {
  return useQuery({
    queryKey: ["dashboard-notifications", "unread-count"],
    queryFn: async (): Promise<number> => {
      if (USE_MOCK_API) return mockDelay(MOCK_UNREAD_COUNT);
      const { data } = await apiClient.get("/notifications/unread-count");
      return data.count ?? 0;
    },
  });
}
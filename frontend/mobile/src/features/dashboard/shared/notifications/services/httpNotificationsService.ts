import { apiGet, apiPost } from "@/services/api/apiClient";

import type { Notification, NotificationCategory } from "../types";

export async function getNotifications(category?: NotificationCategory): Promise<Notification[]> {
  const query = category ? `?category=${category}` : "";
  const data = await apiGet<{ notifications: Notification[] }>(`/notifications${query}`);
  return data.notifications;
}

export async function getUnreadCount(): Promise<number> {
  const data = await apiGet<{ count: number }>("/notifications/unread-count");
  return data.count;
}

export async function markAsRead(notificationId: string): Promise<Notification> {
  return apiPost<Notification>(`/notifications/${notificationId}/read`);
}

export async function markAllAsRead(): Promise<number> {
  const data = await apiPost<{ markedRead: number }>("/notifications/read-all");
  return data.markedRead;
}

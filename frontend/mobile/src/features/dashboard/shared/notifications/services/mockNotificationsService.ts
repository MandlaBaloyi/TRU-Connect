import type { Notification, NotificationCategory } from "../types";

const latency = (ms = 300) => new Promise<void>((resolve) => setTimeout(resolve, ms));

const hoursAgo = (h: number) => new Date(Date.now() - h * 3600_000).toISOString();
const daysAgo = (d: number) => new Date(Date.now() - d * 86_400_000).toISOString();

// Genuinely stateful across calls within this mock session -- mark-as-
// read actually mutates this, same discipline as every other mock
// service in this app.
let notifications: Notification[] = [
  {
    id: "mock-notif-1",
    category: "STOCK_ORDER",
    title: "New order",
    body: "TruConnect: New order TRU-7QXM-4K9P2X from Mandla's Spaza Shop \u00b7 Amount R240.00 \u00b7 Today",
    relatedEntityType: "stock_order",
    relatedEntityId: "mock-cart-sup_001",
    isRead: false,
    createdAt: hoursAgo(0.05),
  },
  {
    id: "mock-notif-2",
    category: "INBOX",
    title: "New connection request",
    body: "TruConnect: Thabo's Wholesale wants to connect with you",
    relatedEntityType: "connection_request",
    relatedEntityId: "mock-request-1",
    isRead: false,
    createdAt: hoursAgo(3),
  },
  {
    id: "mock-notif-3",
    category: "STOCK_ORDER",
    title: "Order confirmed",
    body: "TruConnect: Order TRU-9R2W-QZ8LMN confirmed by Naledi's Café \u00b7 Amount R580.00 \u00b7 Yesterday",
    relatedEntityType: "stock_order",
    relatedEntityId: "mock-cart-sup_002",
    isRead: true,
    createdAt: daysAgo(1),
  },
  {
    id: "mock-notif-4",
    category: "INBOX",
    title: "Connection accepted",
    body: "TruConnect: Sipho's Butchery accepted your connection request",
    relatedEntityType: "connection_request",
    relatedEntityId: "mock-request-2",
    isRead: true,
    createdAt: daysAgo(3),
  },
];

export async function getNotifications(category?: NotificationCategory): Promise<Notification[]> {
  await latency(300);
  const filtered = category ? notifications.filter((n) => n.category === category) : notifications;
  return [...filtered].sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime());
}

export async function getUnreadCount(): Promise<number> {
  await latency(150);
  return notifications.filter((n) => !n.isRead).length;
}

export async function markAsRead(notificationId: string): Promise<Notification> {
  await latency(200);
  const notification = notifications.find((n) => n.id === notificationId);
  if (!notification) throw new Error("Notification not found.");
  notification.isRead = true;
  return notification;
}

export async function markAllAsRead(): Promise<number> {
  await latency(300);
  const count = notifications.filter((n) => !n.isRead).length;
  notifications = notifications.map((n) => ({ ...n, isRead: true }));
  return count;
}

/**
 * shared/notifications -- genuinely role-agnostic, matching
 * shared/connections' own established precedent for a cross-role
 * feature. Communicates with domains/platform/notifications on the
 * backend (/api/v1/notifications routes) -- deliberately no role in
 * this URL prefix at all, matching that domain's own "a notification
 * belongs to whoever it's addressed to" design.
 */

export type NotificationCategory = "STOCK_ORDER" | "INBOX";

export interface Notification {
  id: string;
  category: NotificationCategory;
  title: string;
  body: string;
  /** e.g. "stock_order", "connection_request" -- what a tapped
   *  notification deep-links to. Generic and untyped here on purpose,
   *  matching the backend's own "this table has no real FK into
   *  whatever it's about" design -- see that model's own docstring. */
  relatedEntityType: string | null;
  relatedEntityId: string | null;
  isRead: boolean;
  createdAt: string;
}

/**
 * GET /api/v1/notifications?category=STOCK_ORDER|INBOX -> { notifications: Notification[] }
 * GET /api/v1/notifications/unread-count -> { count: number }
 * POST /api/v1/notifications/{id}/read -> Notification
 * POST /api/v1/notifications/read-all -> { markedRead: number }
 */

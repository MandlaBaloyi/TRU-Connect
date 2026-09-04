import * as mockApi from "./mockNotificationsService";
import * as httpApi from "./httpNotificationsService";

const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

const impl = USE_MOCK ? mockApi : httpApi;

export const getNotifications = impl.getNotifications;
export const getUnreadCount = impl.getUnreadCount;
export const markAsRead = impl.markAsRead;
export const markAllAsRead = impl.markAllAsRead;

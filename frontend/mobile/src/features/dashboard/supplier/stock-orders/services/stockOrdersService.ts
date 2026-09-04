import * as mockApi from "./mockStockOrdersService";
import * as httpApi from "./httpStockOrdersService";

const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

const impl = USE_MOCK ? mockApi : httpApi;

export const getOrders = impl.getOrders;
export const getOrderDetail = impl.getOrderDetail;
export const approveOrder = impl.approveOrder;
export const declineOrder = impl.declineOrder;

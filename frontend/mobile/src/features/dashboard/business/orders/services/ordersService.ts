import * as mockApi from "./mockOrdersService";
import * as httpApi from "./httpOrdersService";

const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

const impl = USE_MOCK ? mockApi : httpApi;

export const getCart = impl.getCart;
export const getMyCarts = impl.getMyCarts;
export const addItem = impl.addItem;
export const updateItemQuantity = impl.updateItemQuantity;
export const removeItem = impl.removeItem;
export const clearCart = impl.clearCart;
export const getOrderHistory = impl.getOrderHistory;
export const getOrderDetail = impl.getOrderDetail;
export const submitCheckout = impl.submitCheckout;

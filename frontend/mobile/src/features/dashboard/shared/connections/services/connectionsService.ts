import * as mockApi from "./mockConnectionsService";
import * as httpApi from "./httpConnectionsService";

const USE_MOCK: boolean = process.env.EXPO_PUBLIC_USE_MOCK_API !== "false";

const impl = USE_MOCK ? mockApi : httpApi;

export const getMyConnections = impl.getMyConnections;
export const getEndedConnections = impl.getEndedConnections;

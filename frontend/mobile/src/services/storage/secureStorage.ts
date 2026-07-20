import * as SecureStore from "expo-secure-store";

/**
 * Thin wrapper around expo-secure-store, used for JWT/refresh token
 * persistence. Ref: docs/04_DATABASE_DESIGN.txt, Section 4.1
 * (Authentication Domain: refresh_tokens)
 */
export const secureStorage = {
  async getItem(key: string): Promise<string | null> {
    return SecureStore.getItemAsync(key);
  },
  async setItem(key: string, value: string): Promise<void> {
    await SecureStore.setItemAsync(key, value);
  },
  async removeItem(key: string): Promise<void> {
    await SecureStore.deleteItemAsync(key);
  },
};

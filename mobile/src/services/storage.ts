import { Platform } from "react-native";

/**
 * Storage abstraction:
 * - Native (iOS/Android): uses expo-secure-store (encrypted)
 * - Web: uses localStorage (fallback)
 */

let SecureStore: typeof import("expo-secure-store") | null = null;

if (Platform.OS !== "web") {
  SecureStore = require("expo-secure-store");
}

async function setItemAsync(key: string, value: string): Promise<void> {
  if (Platform.OS === "web") {
    localStorage.setItem(key, value);
  } else {
    await SecureStore!.setItemAsync(key, value);
  }
}

async function getItemAsync(key: string): Promise<string | null> {
  if (Platform.OS === "web") {
    return localStorage.getItem(key);
  }
  return SecureStore!.getItemAsync(key);
}

async function deleteItemAsync(key: string): Promise<void> {
  if (Platform.OS === "web") {
    localStorage.removeItem(key);
  } else {
    await SecureStore!.deleteItemAsync(key);
  }
}

export default { setItemAsync, getItemAsync, deleteItemAsync };

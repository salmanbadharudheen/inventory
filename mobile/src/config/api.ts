import { Platform } from "react-native";
import Constants from "expo-constants";

const DEFAULT_REMOTE_API_URL = "https://web-production-62fee.up.railway.app";

function normalizeBaseUrl(url: string): string {
  return url.replace(/\/+$/, "");
}

function getExpoHostApiUrl(): string | null {
  const possibleHostUri =
    Constants.expoConfig?.hostUri ??
    (Constants as any).manifest2?.extra?.expoClient?.hostUri ??
    null;

  if (!possibleHostUri) return null;

  const host = String(possibleHostUri).split(":")[0]?.trim();
  if (!host) return null;
  if (host === "localhost" || host === "127.0.0.1") return null;

  return `http://${host}:8000`;
}

function resolveApiUrl(): string {
  if (Platform.OS === "web") {
    return "http://localhost:8000";
  }

  const configured = process.env.EXPO_PUBLIC_API_URL?.trim();
  if (configured) {
    return configured;
  }

  if (__DEV__) {
    const expoHostApiUrl = getExpoHostApiUrl();
    if (expoHostApiUrl) {
      return expoHostApiUrl;
    }
  }

  return DEFAULT_REMOTE_API_URL;
}

// Web runs in the browser on the same machine as Django -> localhost.
// Native development in Expo Go should use the host machine's LAN IP so the
// phone can reach the local Django server. Release builds must use a deployed API.
const API_URL = normalizeBaseUrl(resolveApiUrl());

/** All API paths matching Django backend */
const API = {
  BASE_URL: API_URL,
  AUTH: {
    LOGIN: "/api/v1/auth/login/",
    LOGOUT: "/api/v1/auth/logout/",
    REGISTER: "/api/v1/auth/register/",
    PROFILE: "/api/v1/auth/profile/",
    CHANGE_PASSWORD: "/api/v1/auth/change-password/",
    TOKEN_REFRESH: "/api/v1/auth/token/refresh/",
  },
  DASHBOARD: "/api/v1/dashboard/",
  ASSETS: {
    LIST: "/api/v1/assets/",
    CREATE: "/api/v1/assets/create/",
    LOOKUP: "/api/v1/assets/lookup/",
    DETAIL: "/api/v1/assets/",          // append <uuid>/
    ATTACHMENTS: "/api/v1/assets/",     // append <uuid>/attachments/
    TAGGING_STATUS: "/api/v1/assets/",  // append <uuid>/tagging-status/
    RFID_TAG: "/api/v1/assets/",        // append <uuid>/rfid-tag/
  },
  LOOKUPS: {
    CATEGORIES: "/api/v1/lookups/categories/",
    SUB_CATEGORIES: "/api/v1/lookups/sub-categories/",
    GROUPS: "/api/v1/lookups/groups/",
    SUB_GROUPS: "/api/v1/lookups/sub-groups/",
    COMPANIES: "/api/v1/lookups/companies/",
    REGIONS: "/api/v1/lookups/regions/",
    SITES: "/api/v1/lookups/sites/",
    BUILDINGS: "/api/v1/lookups/buildings/",
    FLOORS: "/api/v1/lookups/floors/",
    BRANCHES: "/api/v1/lookups/branches/",
    DEPARTMENTS: "/api/v1/lookups/departments/",
  },
} as const;

export default API;

import { Platform } from "react-native";

// Web runs in the browser on the same machine as Django → use localhost
// Native runs on a phone on the same LAN → use the LAN IP from .env
const API_URL =
  Platform.OS === "web"
    ? "http://localhost:8000"
    : (process.env.EXPO_PUBLIC_API_URL ?? "http://localhost:8000");

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

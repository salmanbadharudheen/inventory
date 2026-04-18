import API from "../config/api";
import type { LoginResponse, ProfileResponse, Tokens } from "../types/api";
import Storage from "./storage";

const ACCESS_KEY = "access_token";
const REFRESH_KEY = "refresh_token";

/** -------- token helpers -------- */

export async function storeTokens(tokens: Tokens) {
  await Storage.setItemAsync(ACCESS_KEY, tokens.access);
  await Storage.setItemAsync(REFRESH_KEY, tokens.refresh);
}

export async function getAccessToken(): Promise<string | null> {
  return Storage.getItemAsync(ACCESS_KEY);
}

export async function getRefreshToken(): Promise<string | null> {
  return Storage.getItemAsync(REFRESH_KEY);
}

export async function clearTokens() {
  await Storage.deleteItemAsync(ACCESS_KEY);
  await Storage.deleteItemAsync(REFRESH_KEY);
}

/** -------- authenticated fetch wrapper -------- */

const DEFAULT_TIMEOUT = 30_000; // 30 seconds

// Mutex for token refresh — prevents concurrent 401s from triggering multiple refreshes
let refreshPromise: Promise<string | null> | null = null;

async function fetchWithTimeout(
  url: string,
  options: RequestInit = {},
  timeout = DEFAULT_TIMEOUT,
): Promise<Response> {
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), timeout);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } catch (err: any) {
    if (err.name === "AbortError") {
      throw new Error("Request timed out. Please check your connection and try again.");
    }
    throw err;
  } finally {
    clearTimeout(timer);
  }
}

async function authFetch(
  path: string,
  options: RequestInit = {}
): Promise<Response> {
  let token = await getAccessToken();

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(options.headers as Record<string, string>),
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  let res = await fetchWithTimeout(`${API.BASE_URL}${path}`, { ...options, headers });

  // If 401 try refreshing the token once (with mutex to avoid concurrent refreshes)
  if (res.status === 401) {
    if (!refreshPromise) {
      refreshPromise = refreshAccessToken().finally(() => { refreshPromise = null; });
    }
    const refreshed = await refreshPromise;
    if (refreshed) {
      headers["Authorization"] = `Bearer ${refreshed}`;
      res = await fetchWithTimeout(`${API.BASE_URL}${path}`, { ...options, headers });
    }
  }

  return res;
}

/** -------- auth API calls -------- */

export async function login(
  username: string,
  password: string
): Promise<LoginResponse> {
  const res = await fetchWithTimeout(`${API.BASE_URL}${API.AUTH.LOGIN}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });

  if (!res.ok) {
    const err = await res.json();
    throw new Error(
      err.non_field_errors?.[0] ??
        err.detail ??
        "Login failed. Check your credentials."
    );
  }

  const data: LoginResponse = await res.json();
  await storeTokens(data.tokens);
  return data;
}

export async function logout(): Promise<void> {
  const refresh = await getRefreshToken();
  try {
    await authFetch(API.AUTH.LOGOUT, {
      method: "POST",
      body: JSON.stringify({ refresh_token: refresh }),
    });
  } finally {
    await clearTokens();
  }
}

export async function refreshAccessToken(): Promise<string | null> {
  const refresh = await getRefreshToken();
  if (!refresh) return null;

  const res = await fetchWithTimeout(`${API.BASE_URL}${API.AUTH.TOKEN_REFRESH}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh }),
  });

  if (!res.ok) {
    await clearTokens();
    return null;
  }

  const data = await res.json();
  await Storage.setItemAsync(ACCESS_KEY, data.access);
  return data.access;
}

export async function getProfile(): Promise<ProfileResponse> {
  const res = await authFetch(API.AUTH.PROFILE);
  if (!res.ok) throw new Error("Failed to fetch profile");
  return res.json();
}

export { authFetch };

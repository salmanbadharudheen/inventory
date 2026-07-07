import API from "../config/api";
import type { DashboardData } from "../types/api";
import { authFetch } from "./auth-api";
import Storage from "./storage";

const DASHBOARD_CACHE_KEY = "dashboard_cache";

// ── In-memory throttle: prevents duplicate network calls ──
let inFlightPromise: Promise<DashboardData> | null = null;
let lastFetchedData: DashboardData | null = null;
let lastFetchTime = 0;
const MIN_FETCH_INTERVAL = 10_000; // 10 seconds

async function parseJsonOrThrowResponseError(res: Response, fallbackMessage: string) {
  const raw = await res.text();
  const contentType = res.headers.get("content-type") || "unknown";

  try {
    return raw ? JSON.parse(raw) : {};
  } catch {
    const preview = raw.replace(/\s+/g, " ").trim().slice(0, 120);
    throw new Error(
      `${fallbackMessage} Server returned ${contentType} from ${res.url || "the API"} instead of JSON${preview ? `: ${preview}` : "."}`
    );
  }
}

/** Return locally cached dashboard data (if any). */
export async function getCachedDashboard(): Promise<DashboardData | null> {
  // Return in-memory data first (fastest)
  if (lastFetchedData) return lastFetchedData;
  try {
    const raw = await Storage.getItemAsync(DASHBOARD_CACHE_KEY);
    if (raw) return JSON.parse(raw) as DashboardData;
  } catch { /* ignore */ }
  return null;
}

/**
 * Fetch dashboard from API with built-in throttle.
 * - If a fetch is already in-flight, returns the same promise (dedup).
 * - If data was fetched < 10s ago, returns cached data instantly.
 * - Pass force=true to bypass the throttle (pull-to-refresh).
 */
export async function getDashboard(force = false): Promise<DashboardData> {
  const now = Date.now();

  // Return recent data without hitting the network
  if (!force && lastFetchedData && now - lastFetchTime < MIN_FETCH_INTERVAL) {
    return lastFetchedData;
  }

  // De-duplicate concurrent calls
  if (inFlightPromise) return inFlightPromise;

  inFlightPromise = (async () => {
    let res: Response;
    try {
      // Dashboard is heavier than auth/profile endpoints; allow a longer timeout.
      res = await authFetch(API.DASHBOARD, {}, 90_000);
    } catch (err: any) {
      const cached = await getCachedDashboard();
      if (cached) return cached;
      throw new Error(err.message || "Network error. Please check your connection.");
    }
    if (!res.ok) {
      const body = await parseJsonOrThrowResponseError(res, "Failed to fetch dashboard.").catch(() => ({}));
      throw new Error(body.detail || `Failed to fetch dashboard (${res.status})`);
    }
    const data: DashboardData = await parseJsonOrThrowResponseError(
      res,
      "Failed to fetch dashboard."
    ) as DashboardData;

    lastFetchedData = data;
    lastFetchTime = Date.now();

    // Persist for instant next launch
    try {
      await Storage.setItemAsync(DASHBOARD_CACHE_KEY, JSON.stringify(data));
    } catch { /* non-critical */ }

    return data;
  })();

  try {
    return await inFlightPromise;
  } finally {
    inFlightPromise = null;
  }
}

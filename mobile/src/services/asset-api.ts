import API from "../config/api";
import type {
  AssetCreatePayload,
  AssetCreateResponse,
  AssetDetail,
  AssetListResponse,
  CategoryItem,
  LookupItem,
} from "../types/api";
import { authFetch } from "./auth-api";

/* ── Asset CRUD ── */

export async function createAsset(
  payload: AssetCreatePayload
): Promise<AssetCreateResponse> {
  let res: Response;
  try {
    res = await authFetch(API.ASSETS.CREATE, {
      method: "POST",
      body: JSON.stringify(payload),
    });
  } catch (err: any) {
    throw new Error(err.message || "Network error. Please check your connection.");
  }
  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    // Flatten DRF field errors into a readable string
    const msg =
      err.detail ??
      Object.entries(err)
        .map(([k, v]) => `${k}: ${Array.isArray(v) ? v.join(", ") : v}`)
        .join("\n") ??
      "Failed to create asset";
    throw new Error(msg);
  }
  return res.json();
}

export async function listAssets(params?: {
  page?: number;
  status?: string;
  category?: number;
  search?: string;
}): Promise<AssetListResponse> {
  const q = new URLSearchParams();
  if (params?.page) q.set("page", String(params.page));
  if (params?.status) q.set("status", params.status);
  if (params?.category) q.set("category", String(params.category));
  if (params?.search) q.set("search", params.search);
  const url = `${API.ASSETS.LIST}${q.toString() ? "?" + q.toString() : ""}`;
  let res: Response;
  try {
    res = await authFetch(url);
  } catch (err: any) {
    throw new Error(err.message || "Network error");
  }
  if (!res.ok) throw new Error("Failed to fetch assets");
  return res.json();
}

export async function lookupAssetByTag(
  assetTag: string
): Promise<AssetDetail> {
  const url = `${API.ASSETS.LOOKUP}?asset_tag=${encodeURIComponent(assetTag)}`;
  let res: Response;
  try {
    res = await authFetch(url);
  } catch (err: any) {
    throw new Error(err.message || "Network error");
  }
  if (!res.ok) {
    if (res.status === 404) throw new Error("Asset not found");
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? "Failed to look up asset");
  }
  return res.json();
}

export async function getAssetDetail(id: string): Promise<AssetDetail> {
  const url = `${API.ASSETS.DETAIL}${id}/`;
  let res: Response;
  try {
    res = await authFetch(url);
  } catch (err: any) {
    throw new Error(err.message || "Network error");
  }
  if (!res.ok) {
    if (res.status === 404) throw new Error("Asset not found");
    throw new Error("Failed to fetch asset details");
  }
  return res.json();
}

/* ── Lookups (with in-memory cache) ── */

const lookupCache = new Map<string, { data: any[]; ts: number }>();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

async function fetchLookup<T = LookupItem>(
  path: string,
  params?: Record<string, string>
): Promise<T[]> {
  const q = new URLSearchParams(params);
  const url = `${path}${q.toString() ? "?" + q.toString() : ""}`;
  const cacheKey = url;

  const cached = lookupCache.get(cacheKey);
  if (cached && Date.now() - cached.ts < CACHE_TTL) {
    return cached.data as T[];
  }

  try {
    const res = await authFetch(url);
    if (!res.ok) return [];
    const data = await res.json();
    const arr = Array.isArray(data) ? data : [];
    lookupCache.set(cacheKey, { data: arr, ts: Date.now() });
    return arr;
  } catch {
    return [];
  }
}

export function clearLookupCache() {
  lookupCache.clear();
}

export const getCategories = () =>
  fetchLookup<CategoryItem>(API.LOOKUPS.CATEGORIES);

export const getSubCategories = (categoryId?: number) =>
  fetchLookup(
    API.LOOKUPS.SUB_CATEGORIES,
    categoryId ? { category: String(categoryId) } : undefined
  );

export const getGroups = () => fetchLookup(API.LOOKUPS.GROUPS);

export const getSubGroups = (groupId?: number) =>
  fetchLookup(
    API.LOOKUPS.SUB_GROUPS,
    groupId ? { group: String(groupId) } : undefined
  );

export const getCompanies = () => fetchLookup(API.LOOKUPS.COMPANIES);

export const getRegions = () => fetchLookup(API.LOOKUPS.REGIONS);

export const getSites = (regionId?: number) =>
  fetchLookup(
    API.LOOKUPS.SITES,
    regionId ? { region: String(regionId) } : undefined
  );

export const getBuildings = (siteId?: number) =>
  fetchLookup(
    API.LOOKUPS.BUILDINGS,
    siteId ? { site: String(siteId) } : undefined
  );

export const getFloors = (buildingId?: number) =>
  fetchLookup(
    API.LOOKUPS.FLOORS,
    buildingId ? { building: String(buildingId) } : undefined
  );

export const getBranches = () => fetchLookup(API.LOOKUPS.BRANCHES);

export const getDepartments = (branchId?: number) =>
  fetchLookup(
    API.LOOKUPS.DEPARTMENTS,
    branchId ? { branch: String(branchId) } : undefined
  );

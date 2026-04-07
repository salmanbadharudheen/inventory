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
  const res = await authFetch(API.ASSETS.CREATE, {
    method: "POST",
    body: JSON.stringify(payload),
  });
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
  const res = await authFetch(url);
  if (!res.ok) throw new Error("Failed to fetch assets");
  return res.json();
}

export async function lookupAssetByTag(
  assetTag: string
): Promise<AssetDetail> {
  const url = `${API.ASSETS.LOOKUP}?asset_tag=${encodeURIComponent(assetTag)}`;
  const res = await authFetch(url);
  if (!res.ok) {
    if (res.status === 404) throw new Error("Asset not found");
    const err = await res.json().catch(() => ({}));
    throw new Error(err.detail ?? "Failed to look up asset");
  }
  return res.json();
}

export async function getAssetDetail(id: string): Promise<AssetDetail> {
  const url = `${API.ASSETS.DETAIL}${id}/`;
  const res = await authFetch(url);
  if (!res.ok) {
    if (res.status === 404) throw new Error("Asset not found");
    throw new Error("Failed to fetch asset details");
  }
  return res.json();
}

/* ── Lookups ── */

async function fetchLookup<T = LookupItem>(
  path: string,
  params?: Record<string, string>
): Promise<T[]> {
  const q = new URLSearchParams(params);
  const url = `${path}${q.toString() ? "?" + q.toString() : ""}`;
  const res = await authFetch(url);
  if (!res.ok) return [];
  return res.json();
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

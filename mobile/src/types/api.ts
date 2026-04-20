/**
 * Type definitions matching Django API responses
 */

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: "ADMIN" | "EMPLOYEE" | "CHECKER" | "SENIOR_MANAGER";
  organization: number | null;
  branch: number | null;
  department: number | null;
  designation: string;
  employee_id: string;
  date_joined: string;
}

export interface Tokens {
  access: string;
  refresh: string;
}

export interface LoginResponse {
  user: User;
  tokens: Tokens;
  message: string;
}

export interface RegisterResponse {
  user: User;
  tokens: Tokens;
  message: string;
}

export interface ProfileResponse {
  user: User;
}

export interface ErrorResponse {
  [key: string]: string[];
}

export interface CategoryBreakdown {
  name: string;
  count: number;
}

export interface StatusItem {
  status: string;
  code: string;
  count: number;
}

export interface RecentAsset {
  id: string;
  name: string;
  asset_id: string;
  status: string;
  category: string;
}

export interface MasterData {
  groups: number;
  sub_groups: number;
  categories: number;
  sub_categories: number;
  regions: number;
  sites: number;
  buildings: number;
  floors: number;
}

export interface DashboardData {
  total_assets: number;
  active_assets: number;
  assigned_assets: number;
  in_repair_assets: number;
  in_storage_assets: number;
  show_financial: boolean;
  total_value: string;
  total_nbv: string;
  total_depreciation: string;
  depreciation_percentage: number;
  category_breakdown: CategoryBreakdown[];
  status_distribution: StatusItem[];
  recent_assets: RecentAsset[];
  master_data: MasterData;
}

/* ── Lookup items (dropdown pickers) ── */

export interface LookupItem {
  id: number;
  name: string;
  code?: string;
}

export interface CategoryItem extends LookupItem {
  useful_life_years: number;
  depreciation_method: string;
  default_salvage_value: string;
}

/* ── Asset types ── */

export type AssetStatus =
  | "ACTIVE"
  | "IN_STORAGE"
  | "UNDER_MAINTENANCE"
  | "LOST"
  | "STOLEN"
  | "RETIRED";

export type AssetCondition = "NEW" | "USED" | "DAMAGED" | "UNDER_REPAIR";

export type AssetType = "TAGGABLE" | "BUILDING_IMPROVEMENTS" | "NTA" | "CAPEX";

export type DepreciationMethod =
  | "STRAIGHT_LINE"
  | "DOUBLE_DECLINING"
  | "SYD"
  | "UNITS_OF_PRODUCTION";

export interface AssetCreatePayload {
  name: string;
  category: number;
  description?: string;
  short_description?: string;
  serial_number?: string;
  quantity?: number;
  asset_type?: AssetType;
  condition?: AssetCondition;
  status?: AssetStatus;
  // classification
  sub_category?: number | null;
  group?: number | null;
  sub_group?: number | null;
  brand?: string;
  model?: string;
  // ownership
  company?: number | null;
  department?: number | null;
  supplier?: number | null;
  employee_number?: string;
  cost_center?: string;
  // location
  region?: number | null;
  site?: number | null;
  building?: number | null;
  floor?: number | null;
  branch?: number | null;
  // financial
  purchase_date?: string | null;
  purchase_price?: string | null;
  currency?: string;
  invoice_number?: string;
  salvage_value?: string | null;
  useful_life_years?: number | null;
  depreciation_method?: DepreciationMethod;
  // dates
  warranty_start?: string | null;
  warranty_end?: string | null;
  po_number?: string;
  // maintenance
  maintenance_required?: boolean;
  // notes
  notes?: string;
}

export interface AssetDetail {
  id: string;
  name: string;
  asset_tag: string;
  asset_code: string;
  erp_asset_number: string;
  description: string;
  short_description: string;
  serial_number: string;
  quantity: number;
  status: AssetStatus;
  condition: AssetCondition;
  asset_type: AssetType;
  brand: string;
  model: string;
  category: number;
  category_name: string;
  group: number | null;
  group_name: string;
  company: number | null;
  company_name: string;
  site: number | null;
  site_name: string;
  building: number | null;
  building_name: string;
  department: number | null;
  department_name: string;
  assigned_to: number | null;
  assigned_to_name: string;
  purchase_date: string | null;
  purchase_price: string | null;
  currency: string;
  current_value: string;
  accumulated_depreciation: string;
  invoice_number: string;
  warranty_start: string | null;
  warranty_end: string | null;
  po_number: string;
  notes: string;
  image: string | null;
  barcode_image: string | null;
  qr_code_image: string | null;
  created_at: string;
  updated_at: string;
}

export interface AssetCreateResponse {
  detail: string;
  assets: AssetDetail | AssetDetail[];
}

export interface AssetListResponse {
  count: number;
  page: number;
  page_size: number;
  results: AssetDetail[];
}

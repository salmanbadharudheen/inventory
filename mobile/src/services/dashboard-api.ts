import API from "../config/api";
import type { DashboardData } from "../types/api";
import { authFetch } from "./auth-api";

export async function getDashboard(): Promise<DashboardData> {
  const res = await authFetch(API.DASHBOARD);
  if (!res.ok) throw new Error("Failed to fetch dashboard");
  return res.json();
}

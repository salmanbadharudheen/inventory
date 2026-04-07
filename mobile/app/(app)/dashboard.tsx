import React, { useCallback, useEffect, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  RefreshControl,
  ActivityIndicator,
  Platform,
  Dimensions,
} from "react-native";
import { useAuth } from "../../src/context/auth-context";
import { getDashboard } from "../../src/services/dashboard-api";
import type { DashboardData } from "../../src/types/api";
import { router } from "expo-router";

const { width: SCREEN_W } = Dimensions.get("window");

/* ── palette ── */
const C = {
  bg: "#F0F2F8",
  card: "#FFFFFF",
  heroBg: "#4338CA",
  heroAccent: "#6366F1",
  primary: "#4F46E5",
  primarySoft: "#EEF2FF",
  success: "#059669",
  successSoft: "#ECFDF5",
  successBg: "#D1FAE5",
  warning: "#D97706",
  warningSoft: "#FFFBEB",
  warningBg: "#FEF3C7",
  danger: "#DC2626",
  dangerSoft: "#FEF2F2",
  dangerBg: "#FECACA",
  info: "#2563EB",
  infoSoft: "#EFF6FF",
  infoBg: "#DBEAFE",
  text: "#0F172A",
  sub: "#64748B",
  faint: "#94A3B8",
  line: "#F1F5F9",
  border: "#E2E8F0",
};

const STATUS_THEME: Record<string, { bg: string; fg: string; soft: string }> = {
  ACTIVE: { bg: C.successBg, fg: C.success, soft: C.successSoft },
  IN_STORAGE: { bg: C.infoBg, fg: C.info, soft: C.infoSoft },
  UNDER_MAINTENANCE: { bg: C.warningBg, fg: C.warning, soft: C.warningSoft },
  LOST: { bg: C.dangerBg, fg: C.danger, soft: C.dangerSoft },
  STOLEN: { bg: C.dangerBg, fg: C.danger, soft: C.dangerSoft },
  RETIRED: { bg: "#F1F5F9", fg: C.faint, soft: "#F8FAFC" },
};

function short(n: number) {
  if (n >= 1_000_000) return (n / 1_000_000).toFixed(1) + "M";
  if (n >= 1_000) return (n / 1_000).toFixed(1) + "K";
  return String(n);
}

/* ────────── screen ────────── */
export default function DashboardScreen() {
  const { user, signOut } = useAuth();
  const [data, setData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      setError(null);
      setData(await getDashboard());
    } catch (e: any) {
      setError(e.message ?? "Failed to load");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, []);

  useEffect(() => { load(); }, [load]);
  const onRefresh = () => { setRefreshing(true); load(true); };

  if (loading && !data) {
    return (
      <View style={st.splash}>
        <ActivityIndicator size="large" color={C.primary} />
        <Text style={{ color: C.sub, marginTop: 12, fontSize: 14 }}>Loading dashboard...</Text>
      </View>
    );
  }

  if (error && !data) {
    return (
      <View style={st.splash}>
        <View style={st.errorIcon}><Text style={{ color: C.danger, fontSize: 28, fontWeight: "800" }}>!</Text></View>
        <Text style={{ color: C.text, fontSize: 16, fontWeight: "600", marginTop: 16 }}>Something went wrong</Text>
        <Text style={{ color: C.sub, fontSize: 13, marginTop: 4, textAlign: "center" }}>{error}</Text>
        <TouchableOpacity style={st.retryBtn} onPress={() => load()}>
          <Text style={st.retryText}>Try Again</Text>
        </TouchableOpacity>
      </View>
    );
  }

  const d = data!;
  const initials = `${(user?.first_name?.[0] ?? "").toUpperCase()}${(user?.last_name?.[0] ?? "").toUpperCase()}`;
  const fullName = [user?.first_name, user?.last_name].filter(Boolean).join(" ") || "User";

  return (
    <View style={st.root}>
      <ScrollView
        contentContainerStyle={{ paddingBottom: 100 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} tintColor="#FFF" colors={[C.primary]} />}
        showsVerticalScrollIndicator={false}
      >
        {/* ═══ Hero Header ═══ */}
        <View style={st.hero}>
          <View style={st.heroInner}>
            {/* Top row: avatar + logout */}
            <View style={st.heroTop}>
              <View style={st.avatarRow}>
                <View style={st.avatar}>
                  <Text style={st.avatarText}>{initials}</Text>
                </View>
                <View style={{ marginLeft: 14 }}>
                  <Text style={st.heroGreeting}>Welcome back</Text>
                  <Text style={st.heroName}>{fullName}</Text>
                </View>
              </View>
              <TouchableOpacity
                style={st.logoutBtn}
                onPress={async () => { await signOut(); router.replace("/login"); }}
              >
                <Text style={st.logoutText}>Logout</Text>
              </TouchableOpacity>
            </View>

            {/* Big stat row */}
            <View style={st.heroStats}>
              <View style={st.heroStatMain}>
                <Text style={st.heroStatNum}>{short(d.total_assets)}</Text>
                <Text style={st.heroStatLabel}>Total Assets</Text>
              </View>
              <View style={st.heroStatDivider} />
              <View style={st.heroStatSide}>
                <View style={st.heroStatMini}>
                  <View style={[st.miniDot, { backgroundColor: "#34D399" }]} />
                  <Text style={st.miniNum}>{short(d.active_assets)}</Text>
                  <Text style={st.miniLabel}>Active</Text>
                </View>
                <View style={st.heroStatMini}>
                  <View style={[st.miniDot, { backgroundColor: "#60A5FA" }]} />
                  <Text style={st.miniNum}>{short(d.assigned_assets)}</Text>
                  <Text style={st.miniLabel}>Assigned</Text>
                </View>
                <View style={st.heroStatMini}>
                  <View style={[st.miniDot, { backgroundColor: "#FBBF24" }]} />
                  <Text style={st.miniNum}>{short(d.in_repair_assets)}</Text>
                  <Text style={st.miniLabel}>In Repair</Text>
                </View>
              </View>
            </View>
          </View>
        </View>

        {/* ═══ Body ═══ */}
        <View style={st.body}>

          {/* ── Quick Actions ── */}
          <View style={st.quickRow}>
            <TouchableOpacity style={st.quickCard} activeOpacity={0.75} onPress={() => router.push("/(app)/scan-asset")}>
              <View style={[st.quickIconWrap, { backgroundColor: C.primarySoft }]}>
                <View style={[st.quickIconInner, { backgroundColor: C.primary }]}>
                  <Text style={st.quickIconText}>QR</Text>
                </View>
              </View>
              <Text style={st.quickLabel}>Scan Asset</Text>
              <Text style={st.quickSub}>QR / Barcode</Text>
            </TouchableOpacity>
            <TouchableOpacity style={st.quickCard} activeOpacity={0.75} onPress={() => router.push("/(app)/add-asset")}>
              <View style={[st.quickIconWrap, { backgroundColor: C.successSoft }]}>
                <View style={[st.quickIconInner, { backgroundColor: C.success }]}>
                  <Text style={st.quickIconText}>+</Text>
                </View>
              </View>
              <Text style={st.quickLabel}>Add Asset</Text>
              <Text style={st.quickSub}>Create new</Text>
            </TouchableOpacity>
          </View>

          {/* ── Status Overview ── */}
          {d.status_distribution.length > 0 && (
            <View style={st.card}>
              <View style={st.cardHeader}>
                <View style={[st.cardIconDot, { backgroundColor: C.primarySoft }]}>
                  <Text style={{ color: C.primary, fontWeight: "800", fontSize: 12 }}>S</Text>
                </View>
                <Text style={st.cardTitle}>Status Overview</Text>
              </View>
              {d.status_distribution.map((item, idx) => {
                const pct = d.total_assets > 0 ? (item.count / d.total_assets) * 100 : 0;
                const th = STATUS_THEME[item.code] ?? STATUS_THEME.RETIRED;
                return (
                  <View key={item.code} style={[st.statusRow, idx === d.status_distribution.length - 1 && { marginBottom: 0 }]}>
                    <View style={st.statusLeft}>
                      <View style={[st.statusBadge, { backgroundColor: th.soft }]}>
                        <View style={[st.statusBadgeDot, { backgroundColor: th.fg }]} />
                      </View>
                      <Text style={st.statusName} numberOfLines={1}>{item.status}</Text>
                    </View>
                    <View style={st.barOuter}>
                      <View style={[st.barInner, { width: `${Math.max(pct, 3)}%`, backgroundColor: th.fg }]} />
                    </View>
                    <View style={[st.statusCountBg, { backgroundColor: th.soft }]}>
                      <Text style={[st.statusCountText, { color: th.fg }]}>{item.count}</Text>
                    </View>
                  </View>
                );
              })}
            </View>
          )}

          {/* ── Top Categories ── */}
          {d.category_breakdown.length > 0 && (
            <View style={st.card}>
              <View style={st.cardHeader}>
                <View style={[st.cardIconDot, { backgroundColor: "#FEF3C7" }]}>
                  <Text style={{ color: C.warning, fontWeight: "800", fontSize: 12 }}>C</Text>
                </View>
                <Text style={st.cardTitle}>Top Categories</Text>
              </View>
              {d.category_breakdown.map((c, i) => (
                <View key={i} style={[st.catRow, i === d.category_breakdown.length - 1 && { borderBottomWidth: 0, paddingBottom: 0 }]}>
                  <View style={[st.catRank, i === 0 ? { backgroundColor: C.primary } : i === 1 ? { backgroundColor: C.heroAccent } : {}]}>
                    <Text style={[st.catRankText, (i === 0 || i === 1) && { color: "#FFF" }]}>{i + 1}</Text>
                  </View>
                  <Text style={st.catName} numberOfLines={1}>{c.name}</Text>
                  <View style={st.catCountPill}>
                    <Text style={st.catCountText}>{c.count}</Text>
                  </View>
                </View>
              ))}
            </View>
          )}

          {/* ── Recent Assets ── */}
          {d.recent_assets.length > 0 && (
            <View style={st.card}>
              <View style={st.cardHeader}>
                <View style={[st.cardIconDot, { backgroundColor: C.successSoft }]}>
                  <Text style={{ color: C.success, fontWeight: "800", fontSize: 12 }}>R</Text>
                </View>
                <Text style={st.cardTitle}>Recently Added</Text>
              </View>
              {d.recent_assets.map((a, i) => {
                const th = STATUS_THEME[a.status] ?? STATUS_THEME.RETIRED;
                return (
                  <View key={a.id} style={[st.assetRow, i === d.recent_assets.length - 1 && { borderBottomWidth: 0, paddingBottom: 0 }]}>
                    <View style={[st.assetIcon, { backgroundColor: th.soft }]}>
                      <Text style={[st.assetIconText, { color: th.fg }]}>
                        {(a.name?.[0] ?? "A").toUpperCase()}
                      </Text>
                    </View>
                    <View style={{ flex: 1, marginLeft: 12 }}>
                      <Text style={st.assetName} numberOfLines={1}>{a.name}</Text>
                      <Text style={st.assetSub}>{a.category || "No category"} · {a.asset_id}</Text>
                    </View>
                    <View style={[st.chip, { backgroundColor: th.soft }]}>
                      <Text style={[st.chipText, { color: th.fg }]}>
                        {a.status.replace(/_/g, " ")}
                      </Text>
                    </View>
                  </View>
                );
              })}
            </View>
          )}

          {/* ── Master Data ── */}
          <View style={st.card}>
            <View style={st.cardHeader}>
              <View style={[st.cardIconDot, { backgroundColor: C.infoSoft }]}>
                <Text style={{ color: C.info, fontWeight: "800", fontSize: 12 }}>M</Text>
              </View>
              <Text style={st.cardTitle}>Master Data</Text>
            </View>
            <View style={st.masterGrid}>
              <MasterTile label="Groups" value={d.master_data.groups} color="#818CF8" />
              <MasterTile label="Sub-groups" value={d.master_data.sub_groups} color="#A78BFA" />
              <MasterTile label="Categories" value={d.master_data.categories} color="#F472B6" />
              <MasterTile label="Sub-cat." value={d.master_data.sub_categories} color="#FB923C" />
              <MasterTile label="Regions" value={d.master_data.regions} color="#34D399" />
              <MasterTile label="Sites" value={d.master_data.sites} color="#60A5FA" />
              <MasterTile label="Buildings" value={d.master_data.buildings} color="#FBBF24" />
              <MasterTile label="Floors" value={d.master_data.floors} color="#F87171" />
            </View>
          </View>
        </View>
      </ScrollView>

      {/* ═══ FAB ═══ */}
      <TouchableOpacity
        style={st.fab}
        activeOpacity={0.85}
        onPress={() => router.push("/(app)/scan-asset")}
      >
        <Text style={st.fabText}>Scan</Text>
      </TouchableOpacity>
    </View>
  );
}

/* ────── sub-components ────── */

function MasterTile({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <View style={st.masterTile}>
      <View style={[st.masterDot, { backgroundColor: color + "30" }]}>
        <Text style={[st.masterDotNum, { color }]}>{value}</Text>
      </View>
      <Text style={st.masterLabel}>{label}</Text>
    </View>
  );
}

/* ────── styles ────── */
const st = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg },
  splash: { flex: 1, backgroundColor: C.bg, justifyContent: "center", alignItems: "center", padding: 32 },
  errorIcon: {
    width: 56, height: 56, borderRadius: 28, backgroundColor: C.dangerSoft,
    justifyContent: "center", alignItems: "center",
  },
  retryBtn: {
    backgroundColor: C.primary, paddingHorizontal: 32, paddingVertical: 13,
    borderRadius: 12, marginTop: 20,
  },
  retryText: { color: "#FFF", fontWeight: "700", fontSize: 15 },

  /* ── hero ── */
  hero: {
    backgroundColor: C.heroBg,
    paddingTop: Platform.OS === "ios" ? 60 : 44,
    paddingBottom: 32,
    borderBottomLeftRadius: 28,
    borderBottomRightRadius: 28,
  },
  heroInner: { paddingHorizontal: 22 },
  heroTop: { flexDirection: "row", justifyContent: "space-between", alignItems: "center", marginBottom: 28 },
  avatarRow: { flexDirection: "row", alignItems: "center" },
  avatar: {
    width: 48, height: 48, borderRadius: 24,
    backgroundColor: "rgba(255,255,255,0.2)",
    justifyContent: "center", alignItems: "center",
    borderWidth: 2, borderColor: "rgba(255,255,255,0.3)",
  },
  avatarText: { color: "#FFF", fontWeight: "800", fontSize: 17 },
  heroGreeting: { color: "rgba(255,255,255,0.7)", fontSize: 13, fontWeight: "500" },
  heroName: { color: "#FFF", fontSize: 18, fontWeight: "700", marginTop: 1 },
  logoutBtn: {
    paddingHorizontal: 16, paddingVertical: 8, borderRadius: 20,
    backgroundColor: "rgba(255,255,255,0.15)",
  },
  logoutText: { color: "rgba(255,255,255,0.9)", fontSize: 13, fontWeight: "600" },

  heroStats: { flexDirection: "row", alignItems: "center" },
  heroStatMain: { alignItems: "center", paddingRight: 24 },
  heroStatNum: { color: "#FFF", fontSize: 44, fontWeight: "800", letterSpacing: -1 },
  heroStatLabel: { color: "rgba(255,255,255,0.6)", fontSize: 13, marginTop: 2, fontWeight: "500" },
  heroStatDivider: { width: 1, height: 60, backgroundColor: "rgba(255,255,255,0.15)", marginRight: 20 },
  heroStatSide: { flex: 1, gap: 10 },
  heroStatMini: { flexDirection: "row", alignItems: "center", gap: 8 },
  miniDot: { width: 8, height: 8, borderRadius: 4 },
  miniNum: { color: "#FFF", fontSize: 16, fontWeight: "800", minWidth: 32 },
  miniLabel: { color: "rgba(255,255,255,0.55)", fontSize: 12, fontWeight: "500" },

  /* ── body ── */
  body: { paddingHorizontal: 18, marginTop: -12 },

  /* ── quick actions ── */
  quickRow: { flexDirection: "row", gap: 12, marginBottom: 16 },
  quickCard: {
    flex: 1, backgroundColor: C.card, borderRadius: 16, padding: 18,
    alignItems: "center",
    shadowColor: "#4338CA", shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.06, shadowRadius: 12, elevation: 3,
  },
  quickIconWrap: {
    width: 56, height: 56, borderRadius: 18,
    justifyContent: "center", alignItems: "center", marginBottom: 12,
  },
  quickIconInner: {
    width: 36, height: 36, borderRadius: 12,
    justifyContent: "center", alignItems: "center",
  },
  quickIconText: { color: "#FFF", fontWeight: "800", fontSize: 14 },
  quickLabel: { fontSize: 14, fontWeight: "700", color: C.text },
  quickSub: { fontSize: 11, color: C.faint, marginTop: 2 },

  /* ── card ── */
  card: {
    backgroundColor: C.card, borderRadius: 16, padding: 20, marginBottom: 14,
    shadowColor: "#000", shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.04, shadowRadius: 8, elevation: 2,
  },
  cardHeader: { flexDirection: "row", alignItems: "center", marginBottom: 18 },
  cardIconDot: {
    width: 28, height: 28, borderRadius: 8,
    justifyContent: "center", alignItems: "center", marginRight: 10,
  },
  cardTitle: { fontSize: 16, fontWeight: "700", color: C.text },

  /* ── status ── */
  statusRow: { flexDirection: "row", alignItems: "center", marginBottom: 12 },
  statusLeft: { flexDirection: "row", alignItems: "center", width: 140 },
  statusBadge: {
    width: 24, height: 24, borderRadius: 8,
    justifyContent: "center", alignItems: "center", marginRight: 8,
  },
  statusBadgeDot: { width: 8, height: 8, borderRadius: 4 },
  statusName: { fontSize: 13, color: C.text, fontWeight: "500", flex: 1 },
  barOuter: {
    flex: 1, height: 8, backgroundColor: C.line, borderRadius: 4,
    overflow: "hidden", marginHorizontal: 10,
  },
  barInner: { height: 8, borderRadius: 4 },
  statusCountBg: {
    minWidth: 34, paddingHorizontal: 8, paddingVertical: 3,
    borderRadius: 6, alignItems: "center",
  },
  statusCountText: { fontSize: 12, fontWeight: "800" },

  /* ── categories ── */
  catRow: {
    flexDirection: "row", alignItems: "center",
    paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: C.line,
  },
  catRank: {
    width: 28, height: 28, borderRadius: 10, backgroundColor: C.line,
    justifyContent: "center", alignItems: "center", marginRight: 12,
  },
  catRankText: { fontSize: 13, fontWeight: "800", color: C.sub },
  catName: { flex: 1, fontSize: 14, fontWeight: "500", color: C.text },
  catCountPill: {
    backgroundColor: C.line, paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8,
  },
  catCountText: { fontSize: 13, fontWeight: "700", color: C.text },

  /* ── recent assets ── */
  assetRow: {
    flexDirection: "row", alignItems: "center",
    paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: C.line,
  },
  assetIcon: {
    width: 40, height: 40, borderRadius: 12,
    justifyContent: "center", alignItems: "center",
  },
  assetIconText: { fontSize: 16, fontWeight: "800" },
  assetName: { fontSize: 14, fontWeight: "600", color: C.text },
  assetSub: { fontSize: 12, color: C.faint, marginTop: 2 },
  chip: { paddingHorizontal: 10, paddingVertical: 4, borderRadius: 8 },
  chipText: { fontSize: 11, fontWeight: "700", textTransform: "capitalize" },

  /* ── master data ── */
  masterGrid: { flexDirection: "row", flexWrap: "wrap", gap: 10 },
  masterTile: {
    width: "30%" as any, flexGrow: 1, flexBasis: "28%",
    alignItems: "center", paddingVertical: 6,
  },
  masterDot: {
    width: 48, height: 48, borderRadius: 16,
    justifyContent: "center", alignItems: "center", marginBottom: 6,
  },
  masterDotNum: { fontSize: 18, fontWeight: "800" },
  masterLabel: { fontSize: 11, color: C.faint, textAlign: "center", fontWeight: "500" },

  /* ── FAB ── */
  fab: {
    position: "absolute", bottom: 28, right: 22,
    backgroundColor: C.primary, paddingHorizontal: 24, paddingVertical: 14,
    borderRadius: 50, flexDirection: "row", alignItems: "center",
    shadowColor: C.primary, shadowOffset: { width: 0, height: 6 },
    shadowOpacity: 0.35, shadowRadius: 12, elevation: 8,
  },
  fabText: { color: "#FFF", fontSize: 15, fontWeight: "700" },
});

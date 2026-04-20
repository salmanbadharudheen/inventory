import React, { useCallback, useEffect, useState, memo } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Image,
} from "react-native";
import { useLocalSearchParams, router } from "expo-router";
import { lookupAssetByTag, getAssetDetail } from "../../src/services/asset-api";
import type { AssetDetail } from "../../src/types/api";
import API from "../../src/config/api";

const C = {
  primary: "#6366F1",
  primaryLight: "#EEF2FF",
  success: "#10B981",
  warning: "#F59E0B",
  danger: "#EF4444",
  info: "#3B82F6",
  bg: "#F3F4F6",
  white: "#FFFFFF",
  text: "#111827",
  muted: "#6B7280",
  border: "#E5E7EB",
};

const STATUS_CONFIG: Record<string, { color: string; icon: string }> = {
  ACTIVE: { color: C.success, icon: "✅" },
  IN_STORAGE: { color: C.info, icon: "📦" },
  UNDER_MAINTENANCE: { color: C.warning, icon: "🔧" },
  LOST: { color: C.danger, icon: "❌" },
  STOLEN: { color: C.danger, icon: "🚨" },
  RETIRED: { color: C.muted, icon: "🗂️" },
};

const CONDITION_LABELS: Record<string, string> = {
  NEW: "New",
  USED: "Used",
  DAMAGED: "Damaged",
  UNDER_REPAIR: "Under Repair",
};

export default function AssetDetailScreen() {
  const params = useLocalSearchParams<{ asset_tag?: string; asset_id?: string }>();
  const [asset, setAsset] = useState<AssetDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = useCallback(
    async (silent = false) => {
      try {
        if (!silent) setLoading(true);
        setError(null);

        let data: AssetDetail;
        if (params.asset_id) {
          data = await getAssetDetail(params.asset_id);
        } else if (params.asset_tag) {
          data = await lookupAssetByTag(params.asset_tag);
        } else {
          throw new Error("No asset identifier provided.");
        }
        setAsset(data);
      } catch (e: any) {
        setError(e.message ?? "Failed to load asset");
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [params.asset_tag, params.asset_id]
  );

  useEffect(() => {
    load();
  }, [load]);

  const onRefresh = () => {
    setRefreshing(true);
    load(true);
  };

  /* ─── Loading state ─── */
  if (loading && !asset) {
    return (
      <View style={styles.centerContainer}>
        <ActivityIndicator size="large" color={C.primary} />
        <Text style={styles.loadingText}>Looking up asset…</Text>
      </View>
    );
  }

  /* ─── Error state ─── */
  if (error && !asset) {
    return (
      <View style={styles.centerContainer}>
        <Text style={styles.errorIcon}>😕</Text>
        <Text style={styles.errorTitle}>
          {error === "Asset not found" ? "Asset Not Found" : "Error"}
        </Text>
        <Text style={styles.errorText}>
          {error === "Asset not found"
            ? `No asset found with tag "${params.asset_tag ?? params.asset_id}"`
            : error}
        </Text>
        <View style={styles.errorActions}>
          <TouchableOpacity style={styles.retryBtn} onPress={() => load()}>
            <Text style={styles.retryBtnText}>Try Again</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={styles.scanAgainBtn}
            onPress={() => router.push("/(app)/scan-asset")}
          >
            <Text style={styles.scanAgainBtnText}>Scan Another</Text>
          </TouchableOpacity>
        </View>
      </View>
    );
  }

  const a = asset!;
  const statusCfg = STATUS_CONFIG[a.status] ?? { color: C.muted, icon: "❓" };

  /* ─── Helper to build image URL ─── */
  const imageUrl = (path: string | null) => {
    if (!path) return null;
    if (path.startsWith("http")) return path;
    return `${API.BASE_URL}${path}`;
  };

  return (
    <View style={styles.screen}>
      <ScrollView
        contentContainerStyle={styles.scrollContent}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} colors={[C.primary]} />
        }
        showsVerticalScrollIndicator={false}
      >
        {/* ── Status banner ── */}
        <View style={[styles.statusBanner, { backgroundColor: statusCfg.color + "12" }]}>
          <Text style={{ fontSize: 20 }}>{statusCfg.icon}</Text>
          <View style={{ flex: 1, marginLeft: 12 }}>
            <Text style={[styles.statusLabel, { color: statusCfg.color }]}>
              {a.status.replace(/_/g, " ")}
            </Text>
            <Text style={styles.statusSub}>
              Condition: {CONDITION_LABELS[a.condition] ?? a.condition}
            </Text>
          </View>
        </View>

        {/* ── Main Info Card ── */}
        <View style={styles.card}>
          <Text style={styles.assetName}>{a.name}</Text>
          {a.short_description ? (
            <Text style={styles.shortDesc}>{a.short_description}</Text>
          ) : null}

          <View style={styles.tagRow}>
            <View style={styles.tagChip}>
              <Text style={styles.tagChipLabel}>Asset Tag</Text>
              <Text style={styles.tagChipValue}>{a.asset_tag}</Text>
            </View>
            {a.serial_number ? (
              <View style={styles.tagChip}>
                <Text style={styles.tagChipLabel}>Serial No.</Text>
                <Text style={styles.tagChipValue}>{a.serial_number}</Text>
              </View>
            ) : null}
          </View>

          {a.asset_code ? <InfoRow label="Asset Code" value={a.asset_code} /> : null}
          {a.erp_asset_number ? (
            <InfoRow label="ERP Number" value={a.erp_asset_number} />
          ) : null}
        </View>

        {/* ── QR / Barcode Images ── */}
        {(a.qr_code_image || a.barcode_image) && (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>📱  Identification Codes</Text>
            <View style={styles.codeImagesRow}>
              {a.qr_code_image && (
                <View style={styles.codeImageBox}>
                  <Image
                    source={{ uri: imageUrl(a.qr_code_image)! }}
                    style={styles.qrImage}
                    resizeMode="contain"
                  />
                  <Text style={styles.codeLabel}>QR Code</Text>
                </View>
              )}
              {a.barcode_image && (
                <View style={styles.codeImageBox}>
                  <Image
                    source={{ uri: imageUrl(a.barcode_image)! }}
                    style={styles.barcodeImage}
                    resizeMode="contain"
                  />
                  <Text style={styles.codeLabel}>Barcode</Text>
                </View>
              )}
            </View>
          </View>
        )}

        {/* ── Classification ── */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>🏷️  Classification</Text>
          <InfoRow label="Category" value={a.category_name} />
          {a.group_name ? <InfoRow label="Group" value={a.group_name} /> : null}
          {a.brand ? <InfoRow label="Brand" value={a.brand} /> : null}
          {a.model ? <InfoRow label="Model" value={a.model} /> : null}
          {a.asset_type ? (
            <InfoRow label="Type" value={a.asset_type.replace(/_/g, " ")} />
          ) : null}
          <InfoRow label="Quantity" value={String(a.quantity)} />
        </View>

        {/* ── Location ── */}
        {(a.site_name || a.building_name || a.department_name) && (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>📍  Location</Text>
            {a.site_name ? <InfoRow label="Site" value={a.site_name} /> : null}
            {a.building_name ? <InfoRow label="Building" value={a.building_name} /> : null}
            {a.department_name ? <InfoRow label="Department" value={a.department_name} /> : null}
          </View>
        )}

        {/* ── Ownership / Assignment ── */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>👤  Ownership</Text>
          {a.company_name ? <InfoRow label="Company" value={a.company_name} /> : null}
          {a.assigned_to_name ? (
            <InfoRow label="Assigned To" value={a.assigned_to_name} />
          ) : (
            <InfoRow label="Assigned To" value="Unassigned" muted />
          )}
        </View>

        {/* ── Financial ── */}
        {(a.purchase_price || a.current_value) && (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>💰  Financial</Text>
            {a.purchase_price ? (
              <InfoRow
                label="Purchase Price"
                value={`${a.currency ?? "AED"} ${parseFloat(a.purchase_price).toLocaleString()}`}
              />
            ) : null}
            {a.purchase_date ? <InfoRow label="Purchase Date" value={a.purchase_date} /> : null}
            {a.current_value ? (
              <InfoRow
                label="Current Value"
                value={`${a.currency ?? "AED"} ${parseFloat(a.current_value).toLocaleString()}`}
              />
            ) : null}
            {a.accumulated_depreciation ? (
              <InfoRow
                label="Depreciation"
                value={`${a.currency ?? "AED"} ${parseFloat(a.accumulated_depreciation).toLocaleString()}`}
              />
            ) : null}
            {a.invoice_number ? (
              <InfoRow label="Invoice #" value={a.invoice_number} />
            ) : null}
          </View>
        )}

        {/* ── Dates ── */}
        {(a.warranty_start || a.warranty_end || a.po_number) && (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>📅  Dates & References</Text>
            {a.warranty_start ? (
              <InfoRow label="Warranty Start" value={a.warranty_start} />
            ) : null}
            {a.warranty_end ? (
              <InfoRow label="Warranty End" value={a.warranty_end} />
            ) : null}
            {a.po_number ? <InfoRow label="PO Number" value={a.po_number} /> : null}
          </View>
        )}

        {/* ── Description ── */}
        {a.description ? (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>📝  Description</Text>
            <Text style={styles.descText}>{a.description}</Text>
          </View>
        ) : null}

        {/* ── Notes ── */}
        {a.notes ? (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>🗒️  Notes</Text>
            <Text style={styles.descText}>{a.notes}</Text>
          </View>
        ) : null}

        {/* ── Meta ── */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>ℹ️  Record Info</Text>
          <InfoRow label="Created" value={formatDate(a.created_at)} />
          <InfoRow label="Updated" value={formatDate(a.updated_at)} />
        </View>

        {/* ── Scan Another button ── */}
        <TouchableOpacity
          style={styles.scanAnotherFull}
          onPress={() => {
            router.back();
            setTimeout(() => router.push("/(app)/scan-asset"), 100);
          }}
        >
          <Text style={styles.scanAnotherFullIcon}>📷</Text>
          <Text style={styles.scanAnotherFullText}>Scan Another Asset</Text>
        </TouchableOpacity>

        <View style={{ height: 40 }} />
      </ScrollView>
    </View>
  );
}

/* ─── Sub-components ─── */

const InfoRow = memo(function InfoRow({
  label,
  value,
  muted,
}: {
  label: string;
  value: string;
  muted?: boolean;
}) {
  return (
    <View style={styles.infoRow}>
      <Text style={styles.infoLabel}>{label}</Text>
      <Text
        style={[styles.infoValue, muted && { color: C.muted, fontStyle: "italic" }]}
        numberOfLines={2}
      >
        {value}
      </Text>
    </View>
  );
});

function formatDate(iso: string): string {
  if (!iso) return "—";
  const d = new Date(iso);
  return d.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

/* ─── Styles ─── */

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.bg },
  scrollContent: { padding: 16, paddingTop: 8 },

  // Center container (loading/error)
  centerContainer: {
    flex: 1,
    backgroundColor: C.bg,
    justifyContent: "center",
    alignItems: "center",
    padding: 32,
  },
  loadingText: { color: C.muted, marginTop: 12, fontSize: 15 },
  errorIcon: { fontSize: 48, marginBottom: 12 },
  errorTitle: { fontSize: 20, fontWeight: "700", color: C.text, marginBottom: 8 },
  errorText: {
    fontSize: 14,
    color: C.muted,
    textAlign: "center",
    lineHeight: 20,
    marginBottom: 24,
  },
  errorActions: { flexDirection: "row", gap: 12 },
  retryBtn: {
    backgroundColor: C.primary,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 10,
  },
  retryBtnText: { color: C.white, fontWeight: "700", fontSize: 14 },
  scanAgainBtn: {
    backgroundColor: C.white,
    paddingHorizontal: 24,
    paddingVertical: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: C.border,
  },
  scanAgainBtnText: { color: C.text, fontWeight: "700", fontSize: 14 },

  // Status banner
  statusBanner: {
    flexDirection: "row",
    alignItems: "center",
    borderRadius: 14,
    padding: 16,
    marginBottom: 12,
  },
  statusLabel: { fontSize: 16, fontWeight: "700" },
  statusSub: { fontSize: 13, color: C.muted, marginTop: 2 },

  // Card
  card: {
    backgroundColor: C.white,
    borderRadius: 14,
    padding: 18,
    marginBottom: 12,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.04,
    shadowRadius: 6,
    elevation: 1,
  },
  sectionTitle: {
    fontSize: 15,
    fontWeight: "700",
    color: C.text,
    marginBottom: 14,
  },

  // Asset header
  assetName: { fontSize: 22, fontWeight: "800", color: C.text, marginBottom: 4 },
  shortDesc: { fontSize: 14, color: C.muted, marginBottom: 12, lineHeight: 20 },

  // Tag chips
  tagRow: { flexDirection: "row", gap: 10, marginTop: 8, marginBottom: 8, flexWrap: "wrap" },
  tagChip: {
    backgroundColor: C.primaryLight,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 10,
    flex: 1,
    minWidth: 130,
  },
  tagChipLabel: { fontSize: 11, color: C.muted, fontWeight: "600", marginBottom: 2 },
  tagChipValue: { fontSize: 15, fontWeight: "700", color: C.primary },

  // QR / Barcode images
  codeImagesRow: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    gap: 20,
  },
  codeImageBox: {
    alignItems: "center",
    padding: 12,
    backgroundColor: C.bg,
    borderRadius: 12,
  },
  qrImage: { width: 120, height: 120 },
  barcodeImage: { width: 180, height: 60 },
  codeLabel: { fontSize: 12, color: C.muted, marginTop: 8, fontWeight: "600" },

  // Info rows
  infoRow: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "flex-start",
    paddingVertical: 8,
    borderBottomWidth: 0.5,
    borderBottomColor: C.border,
  },
  infoLabel: { fontSize: 13, color: C.muted, fontWeight: "500", flex: 1 },
  infoValue: { fontSize: 14, fontWeight: "600", color: C.text, flex: 1.5, textAlign: "right" },

  // Description
  descText: { fontSize: 14, color: C.text, lineHeight: 22 },

  // Scan another button
  scanAnotherFull: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    backgroundColor: C.primary,
    borderRadius: 14,
    paddingVertical: 16,
    marginTop: 4,
    gap: 10,
  },
  scanAnotherFullIcon: { fontSize: 20 },
  scanAnotherFullText: { color: C.white, fontSize: 16, fontWeight: "700" },
});

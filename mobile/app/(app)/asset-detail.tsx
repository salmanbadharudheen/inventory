import React, { useCallback, useEffect, useRef, useState, memo } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  ActivityIndicator,
  RefreshControl,
  Image,
  Linking,
  Alert,
  Share,
  Modal,
  TextInput,
  Platform,
} from "react-native";
import { useLocalSearchParams, router } from "expo-router";
import * as ImagePicker from "expo-image-picker";
import * as DocumentPicker from "expo-document-picker";
import {
  lookupAssetByTag,
  getAssetDetail,
  listAttachments,
  uploadAttachment,
  deleteAttachment,
  updateTaggingStatus,
} from "../../src/services/asset-api";
import type { AssetAttachment, AssetDetail, AttachmentType } from "../../src/types/api";
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
  const params = useLocalSearchParams<{ asset_tag?: string; asset_id?: string; from_scan?: string }>();
  const [asset, setAsset] = useState<AssetDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Attachments state
  const [attachments, setAttachments] = useState<AssetAttachment[]>([]);
  const [attLoading, setAttLoading] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadType, setUploadType] = useState<AttachmentType>("PHOTO");
  const [uploadDesc, setUploadDesc] = useState("");
  const [pendingFile, setPendingFile] = useState<{ uri: string; name: string; type: string } | null>(null);
  const [uploading, setUploading] = useState(false);

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
        // Load attachments in background
        const atts = await listAttachments(data.id).catch(() => []);
        setAttachments(atts);

        // If opened from scan and asset is not yet tagged, prompt user
        if (params.from_scan === "1" && data.tagging_status === "UNTAGGED") {
          setTimeout(() => {
            Alert.alert(
              "Label Tagged?",
              `Is the physical label tagged on this asset?\n\n${data.name} (${data.asset_tag})`,
              [
                { text: "Not Yet", style: "cancel" },
                {
                  text: "Yes, Tagged ✅",
                  onPress: async () => {
                    try {
                      await updateTaggingStatus(data.id, "TAGGED");
                      setAsset((prev) =>
                        prev ? { ...prev, tagging_status: "TAGGED" } : prev
                      );
                    } catch (e: any) {
                      Alert.alert("Error", e.message ?? "Failed to update tagging status");
                    }
                  },
                },
              ]
            );
          }, 600); // slight delay so screen renders first
        }
      } catch (e: any) {
        setError(e.message ?? "Failed to load asset");
      } finally {
        setLoading(false);
        setRefreshing(false);
      }
    },
    [params.asset_tag, params.asset_id]
  );

  /* ─── Attachment helpers ─── */
  const pickImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== "granted") {
      Alert.alert("Permission required", "Please allow access to your photo library.");
      return;
    }
    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: false,
      quality: 0.85,
    });
    if (!result.canceled && result.assets.length > 0) {
      const asset = result.assets[0];
      const name = asset.fileName ?? `photo_${Date.now()}.jpg`;
      const type = asset.mimeType ?? "image/jpeg";
      setPendingFile({ uri: asset.uri, name, type });
      setUploadType("PHOTO");
      setShowUploadModal(true);
    }
  };

  const pickCamera = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== "granted") {
      Alert.alert("Permission required", "Please allow camera access.");
      return;
    }
    const result = await ImagePicker.launchCameraAsync({
      allowsEditing: false,
      quality: 0.85,
    });
    if (!result.canceled && result.assets.length > 0) {
      const asset = result.assets[0];
      const name = asset.fileName ?? `photo_${Date.now()}.jpg`;
      const type = asset.mimeType ?? "image/jpeg";
      setPendingFile({ uri: asset.uri, name, type });
      setUploadType("PHOTO");
      setShowUploadModal(true);
    }
  };

  const pickDocument = async () => {
    const result = await DocumentPicker.getDocumentAsync({
      type: [
        "application/pdf",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.ms-excel",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "text/plain",
        "image/*",
      ],
      copyToCacheDirectory: true,
    });
    if (!result.canceled && result.assets.length > 0) {
      const doc = result.assets[0];
      setPendingFile({ uri: doc.uri, name: doc.name, type: doc.mimeType ?? "application/octet-stream" });
      setUploadType("OTHER");
      setShowUploadModal(true);
    }
  };

  const handleUpload = async () => {
    if (!pendingFile || !asset) return;
    setUploading(true);
    try {
      const att = await uploadAttachment(asset.id, pendingFile, uploadType, uploadDesc || undefined);
      setAttachments((prev) => [att, ...prev]);
      setShowUploadModal(false);
      setPendingFile(null);
      setUploadDesc("");
    } catch (e: any) {
      Alert.alert("Upload failed", e.message ?? "Unknown error");
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = (att: AssetAttachment) => {
    Alert.alert("Delete attachment?", att.attachment_type_display + (att.description ? ` — ${att.description}` : ""), [
      { text: "Cancel", style: "cancel" },
      {
        text: "Delete",
        style: "destructive",
        onPress: async () => {
          if (!asset) return;
          try {
            await deleteAttachment(asset.id, att.id);
            setAttachments((prev) => prev.filter((a) => a.id !== att.id));
          } catch (e: any) {
            Alert.alert("Error", e.message ?? "Failed to delete");
          }
        },
      },
    ]);
  };

  const showAddOptions = () => {
    Alert.alert("Add Attachment", "Choose a source", [
      { text: "📷 Take Photo", onPress: pickCamera },
      { text: "🖼️ Photo Library", onPress: pickImage },
      { text: "📄 Document / File", onPress: pickDocument },
      { text: "Cancel", style: "cancel" },
    ]);
  };

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

  /* ─── Open a document/file URL in browser or external app ─── */
  const openFile = async (path: string | null) => {
    const url = imageUrl(path);
    if (!url) return;
    try {
      const can = await Linking.canOpenURL(url);
      if (!can) throw new Error("Cannot open URL");
      await Linking.openURL(url);
    } catch (e) {
      Alert.alert("Cannot open file", "No app available to open this file.");
    }
  };

  /* ─── Share / copy a file URL via the system share sheet ─── */
  const shareFile = async (path: string | null, label: string) => {
    const url = imageUrl(path);
    if (!url) return;
    try {
      await Share.share({
        message: `${a.name} — ${label}\n${url}`,
        url, // iOS uses this for proper link sharing
        title: `${a.name} — ${label}`,
      });
    } catch (e: any) {
      Alert.alert("Cannot share", e?.message ?? "Failed to share link.");
    }
  };

  /* ─── Filename from a path ─── */
  const fileName = (path: string | null) => {
    if (!path) return "";
    const segs = path.split("/");
    return decodeURIComponent(segs[segs.length - 1] || "file");
  };

  /* ─── Document fields list ─── */
  const documents: { label: string; icon: string; path: string | null }[] = [
    { label: "Purchase Order", icon: "🧾", path: a.po_file },
    { label: "Invoice", icon: "💳", path: a.invoice_file },
    { label: "Delivery Note", icon: "📦", path: a.delivery_note_file },
    { label: "Insurance", icon: "🛡️", path: a.insurance_file },
    { label: "AMC Contract", icon: "📑", path: a.amc_file },
  ].filter((d) => !!d.path);

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

        {/* ── Asset Photo ── */}
        {a.image && (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>🖼️  Asset Photo</Text>
            <TouchableOpacity activeOpacity={0.85} onPress={() => openFile(a.image)}>
              <Image
                source={{ uri: imageUrl(a.image)! }}
                style={styles.assetPhoto}
                resizeMode="cover"
              />
            </TouchableOpacity>
            <View style={styles.photoActions}>
              <TouchableOpacity
                style={styles.photoActionBtn}
                onPress={() => openFile(a.image)}
              >
                <Text style={styles.photoActionText}>Open</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.photoActionBtn, styles.photoActionBtnAlt]}
                onPress={() => shareFile(a.image, "Photo")}
              >
                <Text style={[styles.photoActionText, styles.photoActionTextAlt]}>
                  🔗 Share Link
                </Text>
              </TouchableOpacity>
            </View>
          </View>
        )}

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

        {/* ── Documents ── */}
        {documents.length > 0 && (
          <View style={styles.card}>
            <Text style={styles.sectionTitle}>📎  Documents</Text>
            {documents.map((doc) => (
              <View key={doc.label} style={styles.docRow}>
                <TouchableOpacity
                  style={styles.docMain}
                  onPress={() => openFile(doc.path)}
                  activeOpacity={0.7}
                >
                  <Text style={styles.docIcon}>{doc.icon}</Text>
                  <View style={{ flex: 1 }}>
                    <Text style={styles.docLabel}>{doc.label}</Text>
                    <Text style={styles.docFile} numberOfLines={1}>
                      {fileName(doc.path)}
                    </Text>
                  </View>
                  <Text style={styles.docOpen}>Open</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.docShareBtn}
                  onPress={() => shareFile(doc.path, doc.label)}
                  activeOpacity={0.7}
                  hitSlop={8}
                >
                  <Text style={styles.docShareIcon}>🔗</Text>
                  <Text style={styles.docShareText}>Share</Text>
                </TouchableOpacity>
              </View>
            ))}
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
          {a.label_type ? (
            <InfoRow label="Label Type" value={a.label_type.replace(/_/g, " ")} />
          ) : null}
          <InfoRow
            label="Tagging Status"
            value={a.tagging_status === "TAGGED" ? "✅ Tagged" : "🏷️ Untagged"}
          />
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

        {/* ── Attachments ── */}
        <View style={styles.card}>
          <View style={styles.attHeader}>
            <Text style={styles.sectionTitle}>📎  Attachments</Text>
            <TouchableOpacity style={styles.attAddBtn} onPress={showAddOptions} activeOpacity={0.75}>
              <Text style={styles.attAddBtnText}>+ Add</Text>
            </TouchableOpacity>
          </View>

          {attachments.length === 0 ? (
            <View style={styles.attEmpty}>
              <Text style={styles.attEmptyText}>No attachments yet.</Text>
              <Text style={styles.attEmptyHint}>Tap + Add to upload a photo or document.</Text>
            </View>
          ) : (
            attachments.map((att) => (
              <View key={att.id} style={styles.attRow}>
                <Text style={styles.attTypeIcon}>
                  {att.attachment_type === "PHOTO" ? "🖼️" : "📄"}
                </Text>
                <View style={{ flex: 1 }}>
                  <Text style={styles.attTypeLabel}>{att.attachment_type_display}</Text>
                  {att.description ? (
                    <Text style={styles.attDesc} numberOfLines={1}>{att.description}</Text>
                  ) : null}
                  <Text style={styles.attDate}>{formatDate(att.created_at)}</Text>
                </View>
                <TouchableOpacity
                  style={styles.attOpenBtn}
                  onPress={() => openFile(att.file_url)}
                  activeOpacity={0.7}
                >
                  <Text style={styles.attOpenText}>Open</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={styles.attDeleteBtn}
                  onPress={() => handleDelete(att)}
                  activeOpacity={0.7}
                  hitSlop={8}
                >
                  <Text style={styles.attDeleteText}>🗑️</Text>
                </TouchableOpacity>
              </View>
            ))
          )}
        </View>

        {/* ── Upload Modal ── */}
        <Modal
          visible={showUploadModal}
          transparent
          animationType="slide"
          onRequestClose={() => { if (!uploading) { setShowUploadModal(false); setPendingFile(null); } }}
        >
          <View style={styles.modalOverlay}>
            <View style={styles.modalBox}>
              <Text style={styles.modalTitle}>Upload Attachment</Text>

              {pendingFile ? (
                <Text style={styles.modalFileName} numberOfLines={1}>
                  📎 {pendingFile.name}
                </Text>
              ) : null}

              {/* Type selector */}
              <Text style={styles.modalLabel}>Type</Text>
              <View style={styles.typeRow}>
                {(["PHOTO", "INVOICE", "WARRANTY", "MANUAL", "OTHER"] as AttachmentType[]).map((t) => (
                  <TouchableOpacity
                    key={t}
                    style={[styles.typeChip, uploadType === t && styles.typeChipActive]}
                    onPress={() => setUploadType(t)}
                    activeOpacity={0.75}
                  >
                    <Text style={[styles.typeChipText, uploadType === t && styles.typeChipTextActive]}>
                      {t}
                    </Text>
                  </TouchableOpacity>
                ))}
              </View>

              {/* Description */}
              <Text style={styles.modalLabel}>Description (optional)</Text>
              <TextInput
                style={styles.modalInput}
                value={uploadDesc}
                onChangeText={setUploadDesc}
                placeholder="e.g. Annual maintenance contract"
                placeholderTextColor={C.muted}
                editable={!uploading}
              />

              <View style={styles.modalActions}>
                <TouchableOpacity
                  style={[styles.modalCancelBtn, uploading && { opacity: 0.5 }]}
                  onPress={() => { if (!uploading) { setShowUploadModal(false); setPendingFile(null); } }}
                  disabled={uploading}
                >
                  <Text style={styles.modalCancelText}>Cancel</Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.modalUploadBtn, (!pendingFile || uploading) && { opacity: 0.5 }]}
                  onPress={handleUpload}
                  disabled={!pendingFile || uploading}
                >
                  {uploading ? (
                    <ActivityIndicator color={C.white} size="small" />
                  ) : (
                    <Text style={styles.modalUploadText}>Upload</Text>
                  )}
                </TouchableOpacity>
              </View>
            </View>
          </View>
        </Modal>

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

  // Asset photo
  assetPhoto: {
    width: "100%",
    height: 220,
    borderRadius: 12,
    backgroundColor: C.bg,
  },
  tapHint: {
    fontSize: 12,
    color: C.muted,
    textAlign: "center",
    marginTop: 8,
    fontStyle: "italic",
  },
  photoActions: {
    flexDirection: "row",
    gap: 8,
    marginTop: 12,
  },
  photoActionBtn: {
    flex: 1,
    paddingVertical: 10,
    borderRadius: 8,
    backgroundColor: C.primary,
    alignItems: "center",
  },
  photoActionBtnAlt: {
    backgroundColor: C.primaryLight,
  },
  photoActionText: { color: C.white, fontWeight: "700", fontSize: 13 },
  photoActionTextAlt: { color: C.primary },

  // Documents
  docRow: {
    paddingVertical: 12,
    borderBottomWidth: 0.5,
    borderBottomColor: C.border,
  },
  docMain: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
  },
  docIcon: { fontSize: 22 },
  docLabel: { fontSize: 14, fontWeight: "700", color: C.text },
  docFile: { fontSize: 12, color: C.muted, marginTop: 2 },
  docOpen: { fontSize: 13, fontWeight: "700", color: C.primary },
  docShareBtn: {
    alignSelf: "flex-start",
    flexDirection: "row",
    alignItems: "center",
    gap: 6,
    marginTop: 8,
    marginLeft: 34,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: C.primaryLight,
  },
  docShareIcon: { fontSize: 13 },
  docShareText: { fontSize: 12, fontWeight: "700", color: C.primary },

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

  // Attachments section
  attHeader: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    marginBottom: 14,
  },
  attAddBtn: {
    backgroundColor: C.primary,
    paddingHorizontal: 14,
    paddingVertical: 6,
    borderRadius: 8,
  },
  attAddBtnText: { color: C.white, fontWeight: "700", fontSize: 13 },
  attEmpty: { alignItems: "center", paddingVertical: 20 },
  attEmptyText: { color: C.muted, fontSize: 14, fontWeight: "600" },
  attEmptyHint: { color: C.muted, fontSize: 12, marginTop: 4 },
  attRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 10,
    paddingVertical: 10,
    borderBottomWidth: 0.5,
    borderBottomColor: C.border,
  },
  attTypeIcon: { fontSize: 22 },
  attTypeLabel: { fontSize: 13, fontWeight: "700", color: C.text },
  attDesc: { fontSize: 12, color: C.muted, marginTop: 1 },
  attDate: { fontSize: 11, color: C.muted, marginTop: 2 },
  attOpenBtn: {
    backgroundColor: C.primaryLight,
    paddingHorizontal: 10,
    paddingVertical: 6,
    borderRadius: 7,
  },
  attOpenText: { color: C.primary, fontWeight: "700", fontSize: 12 },
  attDeleteBtn: { padding: 4 },
  attDeleteText: { fontSize: 16 },

  // Upload modal
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.5)",
    justifyContent: "flex-end",
  },
  modalBox: {
    backgroundColor: C.white,
    borderTopLeftRadius: 20,
    borderTopRightRadius: 20,
    padding: 24,
    paddingBottom: 36,
  },
  modalTitle: { fontSize: 18, fontWeight: "800", color: C.text, marginBottom: 16 },
  modalFileName: {
    fontSize: 13,
    color: C.muted,
    backgroundColor: C.bg,
    padding: 10,
    borderRadius: 8,
    marginBottom: 14,
  },
  modalLabel: { fontSize: 12, fontWeight: "700", color: C.muted, marginBottom: 6, marginTop: 10 },
  typeRow: { flexDirection: "row", flexWrap: "wrap", gap: 8 },
  typeChip: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    borderWidth: 1,
    borderColor: C.border,
    backgroundColor: C.bg,
  },
  typeChipActive: { backgroundColor: C.primary, borderColor: C.primary },
  typeChipText: { fontSize: 12, fontWeight: "600", color: C.muted },
  typeChipTextActive: { color: C.white },
  modalInput: {
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 8,
    padding: 10,
    fontSize: 14,
    color: C.text,
    backgroundColor: C.bg,
    marginTop: 4,
  },
  modalActions: {
    flexDirection: "row",
    gap: 10,
    marginTop: 20,
  },
  modalCancelBtn: {
    flex: 1,
    paddingVertical: 12,
    borderRadius: 10,
    borderWidth: 1,
    borderColor: C.border,
    alignItems: "center",
  },
  modalCancelText: { fontWeight: "700", color: C.text, fontSize: 14 },
  modalUploadBtn: {
    flex: 2,
    paddingVertical: 12,
    borderRadius: 10,
    backgroundColor: C.primary,
    alignItems: "center",
  },
  modalUploadText: { fontWeight: "700", color: C.white, fontSize: 14 },
});

import React, { useCallback, useEffect, useRef, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  TextInput,
  KeyboardAvoidingView,
  Platform,
  Modal,
} from "react-native";
import { Camera, CameraView, useCameraPermissions } from "expo-camera";
import { router } from "expo-router";
import { lookupAssetByRfidTag } from "../../src/services/asset-api";
import { rfidManager } from "../../src/rfid";
import type { ReaderInfo } from "../../src/rfid";

function normalizeScannedIdentifier(value: string, isQr: boolean): string {
  let normalized = (value || "").trim();

  if (!isQr) {
    // Code39 scanners may include * start/stop guards.
    normalized = normalized.replace(/^\*+|\*+$/g, "");
  }

  // Some camera decoders append punctuation for tiny/blurred labels.
  normalized = normalized.replace(/[\s.,;:!"'`]+$/g, "");

  return normalized;
}

function normalizeRfidIdentifier(value: string): string {
  return normalizeScannedIdentifier(value, true).replace(/[\s:-]+/g, "").toUpperCase();
}

/* ─── Exported screen ─── */
export default function ScanAssetScreen() {
  const [permission, requestPermission] = useCameraPermissions();
  const [scanned, setScanned] = useState(false);
  const [showManualEntry, setShowManualEntry] = useState(false);
  const [manualValue, setManualValue] = useState("");
  const [searchMode, setSearchMode] = useState<"tag" | "id" | "rfid">("tag");
  const [cameraReady, setCameraReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [availableReaders, setAvailableReaders] = useState<ReaderInfo[]>([]);
  const [selectedReaderId, setSelectedReaderId] = useState<string | null>(null);
  const [rfidSupported, setRfidSupported] = useState<boolean | null>(null);
  const [rfidBusy, setRfidBusy] = useState(false);
  const [lastRfidValue, setLastRfidValue] = useState<string | null>(null);
  const [showReaderModal, setShowReaderModal] = useState(false);
  const processingRef = useRef(false);

  useEffect(() => {
    let mounted = true;

    (async () => {
      try {
        const readers = rfidManager.getAvailableReaders();
        const selected = rfidManager.getSelectedReader();
        if (!mounted) return;
        setAvailableReaders(readers);
        setSelectedReaderId(selected?.id ?? null);

        if (!selected) {
          setRfidSupported(false);
          return;
        }

        const supported = await rfidManager.isSelectedReaderSupported();
        setRfidSupported(supported);
      } catch {
        if (mounted) {
          setRfidSupported(false);
        }
      }
    })();

    return () => {
      mounted = false;
      rfidManager.stopScan().catch(() => undefined);
      rfidManager.disconnect().catch(() => undefined);
    };
  }, []);

  const navigateToDetail = useCallback((assetTag: string) => {
    router.push({
      pathname: "/(app)/asset-detail",
      params: { asset_tag: assetTag, from_scan: "1" },
    });
  }, []);

  const navigateToDetailById = useCallback((assetId: string) => {
    router.push({
      pathname: "/(app)/asset-detail",
      params: { asset_id: assetId, from_scan: "1" },
    });
  }, []);

  const handleRfidLookup = useCallback(async (rfidValue: string) => {
    const asset = await lookupAssetByRfidTag(rfidValue);
    router.push({
      pathname: "/(app)/asset-detail",
      params: { asset_id: asset.id, from_scan: "1" },
    });
  }, []);

  const onSelectReader = useCallback(async (readerId: string) => {
    try {
      await rfidManager.stopScan().catch(() => undefined);
      await rfidManager.disconnect().catch(() => undefined);
      rfidManager.selectReader(readerId);
      const selected = rfidManager.getSelectedReader();
      setSelectedReaderId(selected?.id ?? null);
      const supported = await rfidManager.isSelectedReaderSupported();
      setRfidSupported(supported);
      setShowReaderModal(false);
    } catch (e: any) {
      Alert.alert("Reader Selection Failed", e?.message ?? "Unable to switch RFID reader.");
    }
  }, []);

  const startRfidScan = useCallback(async () => {
    if (rfidBusy) return;

    const selected = rfidManager.getSelectedReader();
    if (!selected) {
      Alert.alert("RFID Reader Not Configured", "No RFID reader adapter is configured.");
      return;
    }

    if (rfidSupported === false) {
      Alert.alert(
        "RFID Not Available",
        `${selected.name} is not supported in this build. Choose another reader adapter or add the vendor SDK module.`
      );
      return;
    }

    setRfidBusy(true);
    setLastRfidValue(null);

    try {
      const unsubscribe = rfidManager.onRead(async (read) => {
        const epc = normalizeRfidIdentifier(read.epc);
        if (!epc) return;

        setLastRfidValue(epc);
        try {
          await handleRfidLookup(epc);
        } catch {
          Alert.alert("Unknown RFID Tag", "Asset Not Registered.");
        } finally {
          await rfidManager.stopScan().catch(() => undefined);
          unsubscribe();
          setRfidBusy(false);
        }
      });

      await rfidManager.connect();
      await rfidManager.startScan();
    } catch (err: any) {
      const message = String(err?.message || err || "");
      if (!/cancel|close|dismiss|abort/i.test(message)) {
        Alert.alert("RFID Scan Failed", message || "Unable to read the RFID tag.");
      }
      await rfidManager.stopScan().catch(() => undefined);
      await rfidManager.disconnect().catch(() => undefined);
      setRfidBusy(false);
    } finally {
      // Keep cleanup in success/error paths where listener lifecycle is controlled.
    }
  }, [handleRfidLookup, rfidBusy, rfidSupported]);

  const handleBarcodeScanned = useCallback(
    ({ type, data }: { type: string; data: string }) => {
      if (processingRef.current) return;
      processingRef.current = true;
      setScanned(true);

      const normalizedType = (type || "").toLowerCase();
      const isQr = normalizedType.includes("qr");
      const scannedValue = normalizeScannedIdentifier(data || "", isQr);
      if (!scannedValue) {
        Alert.alert("Invalid Code", "The scanned code is empty.", [
          {
            text: "Scan Again",
            onPress: () => {
              setScanned(false);
              processingRef.current = false;
            },
          },
        ]);
        return;
      }

      if (scannedValue.toLowerCase() === "undefined" || scannedValue.toLowerCase() === "null") {
        Alert.alert("Invalid Code", "The scanned code is invalid. Please scan again.", [
          {
            text: "Scan Again",
            onPress: () => {
              setScanned(false);
              processingRef.current = false;
            },
          },
        ]);
        return;
      }

      // QR codes encode the human-readable asset tag.
      // Linear barcodes can now encode compact payloads, so they must use
      // barcode_tag lookup on the detail screen/API.
      router.push({
        pathname: "/(app)/asset-detail",
        params: isQr
          ? { asset_tag: scannedValue, from_scan: "1" }
          : { barcode_tag: scannedValue, from_scan: "1" },
      });
      setTimeout(() => {
        processingRef.current = false;
      }, 1500);
    },
    []
  );

  const handleManualSubmit = () => {
    const value = manualValue.trim();
    if (!value) {
      Alert.alert("Required", searchMode === "tag" ? "Please enter an asset tag." : searchMode === "rfid" ? "Please enter an RFID tag." : "Please enter an asset ID.");
      return;
    }
    if (searchMode === "id") {
      navigateToDetailById(value);
    } else if (searchMode === "rfid") {
      const normalizedValue = normalizeRfidIdentifier(value);
      lookupAssetByRfidTag(normalizedValue)
        .then((asset) => {
          router.push({
            pathname: "/(app)/asset-detail",
            params: { asset_id: asset.id, from_scan: "1" },
          });
        })
        .catch((err: any) => {
          Alert.alert("Not Found", err.message ?? "No asset found with that RFID tag.");
        });
    } else {
      navigateToDetail(value);
    }
  };

  /* ── Error screen ── */
  if (error) {
    return (
      <View style={s.centerContainer}>
        <Text style={s.title}>Camera Error</Text>
        <Text style={s.subtitle}>{error}</Text>
        <TouchableOpacity style={s.btn} onPress={() => setError(null)}>
          <Text style={s.btnText}>Retry</Text>
        </TouchableOpacity>
        <TouchableOpacity style={s.secondaryBtn} onPress={startRfidScan} disabled={rfidBusy}>
          <Text style={s.secondaryBtnText}>{rfidBusy ? "Reading RFID..." : "Scan RFID Tag"}</Text>
        </TouchableOpacity>
        <TouchableOpacity style={s.secondaryBtn} onPress={() => setShowReaderModal(true)} disabled={rfidBusy}>
          <Text style={s.secondaryBtnText}>Select RFID Reader</Text>
        </TouchableOpacity>
        <TouchableOpacity style={s.btn} onPress={() => setShowManualEntry(true)}>
          <Text style={s.btnText}>Find Asset Manually</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={s.linkText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  /* ── Permission: loading ── */
  if (!permission) {
    return (
      <View style={s.centerContainer}>
        <ActivityIndicator size="large" color="#6366F1" />
        <TouchableOpacity style={s.secondaryBtn} onPress={startRfidScan} disabled={rfidBusy}>
          <Text style={s.secondaryBtnText}>{rfidBusy ? "Reading RFID..." : "Scan RFID Tag"}</Text>
        </TouchableOpacity>
        <TouchableOpacity style={s.secondaryBtn} onPress={() => setShowReaderModal(true)} disabled={rfidBusy}>
          <Text style={s.secondaryBtnText}>Select RFID Reader</Text>
        </TouchableOpacity>
      </View>
    );
  }

  /* ── Permission: not granted ── */
  if (!permission.granted) {
    return (
      <View style={s.centerContainer}>
        <Text style={s.title}>Camera Permission Required</Text>
        <Text style={s.subtitle}>
          Allow camera access to scan QR codes and barcodes on assets.
        </Text>
        <TouchableOpacity style={s.btn} onPress={requestPermission}>
          <Text style={s.btnText}>Grant Permission</Text>
        </TouchableOpacity>
        <TouchableOpacity style={s.secondaryBtn} onPress={startRfidScan} disabled={rfidBusy}>
          <Text style={s.secondaryBtnText}>{rfidBusy ? "Reading RFID..." : "Scan RFID Tag"}</Text>
        </TouchableOpacity>
        <TouchableOpacity style={s.secondaryBtn} onPress={() => setShowReaderModal(true)} disabled={rfidBusy}>
          <Text style={s.secondaryBtnText}>Select RFID Reader</Text>
        </TouchableOpacity>
        <TouchableOpacity style={s.secondaryBtn} onPress={() => setShowManualEntry(true)}>
          <Text style={s.secondaryBtnText}>Find Asset Manually</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={() => router.back()}>
          <Text style={s.linkText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  /* ── Manual entry ── */
  if (showManualEntry) {
    return (
      <KeyboardAvoidingView
        style={s.centerContainer}
        behavior={Platform.OS === "ios" ? "padding" : undefined}
      >
        <View style={s.card}>
          <Text style={s.title}>Find Asset</Text>

          {/* Mode toggle */}
          <View style={s.toggleRow}>
            <TouchableOpacity
              style={[s.toggleBtn, searchMode === "tag" && s.toggleBtnActive]}
              onPress={() => { setSearchMode("tag"); setManualValue(""); }}
            >
              <Text style={[s.toggleBtnText, searchMode === "tag" && s.toggleBtnTextActive]}>
                Asset Tag
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[s.toggleBtn, searchMode === "id" && s.toggleBtnActive]}
              onPress={() => { setSearchMode("id"); setManualValue(""); }}
            >
              <Text style={[s.toggleBtnText, searchMode === "id" && s.toggleBtnTextActive]}>
                Asset ID
              </Text>
            </TouchableOpacity>
            <TouchableOpacity
              style={[s.toggleBtn, searchMode === "rfid" && s.toggleBtnActive]}
              onPress={() => { setSearchMode("rfid"); setManualValue(""); }}
            >
              <Text style={[s.toggleBtnText, searchMode === "rfid" && s.toggleBtnTextActive]}>
                RFID Tag
              </Text>
            </TouchableOpacity>
          </View>

          <Text style={s.subtitle}>
            {searchMode === "tag"
              ? "Type the asset tag printed below the barcode"
              : searchMode === "rfid"
              ? "Enter the RFID tag number (e.g. E20034120123456789ABCDEF)"
              : "Enter the numeric/UUID asset ID"}
          </Text>

          <TextInput
            style={s.input}
            value={manualValue}
            onChangeText={setManualValue}
            placeholder={searchMode === "tag" ? "e.g. ABC-0001-26" : searchMode === "rfid" ? "e.g. E20034120123456789ABCDEF" : "e.g. 1042 or UUID"}
            placeholderTextColor="#9CA3AF"
            autoCapitalize={searchMode === "tag" || searchMode === "rfid" ? "characters" : "none"}
            autoCorrect={false}
            autoFocus
            returnKeyType="search"
            onSubmitEditing={handleManualSubmit}
          />
          <TouchableOpacity style={s.btn} onPress={handleManualSubmit}>
            <Text style={s.btnText}>Look Up Asset</Text>
          </TouchableOpacity>
          <TouchableOpacity
            onPress={() => {
              setShowManualEntry(false);
              setManualValue("");
            }}
          >
            <Text style={s.linkText}>Back to Scanner</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    );
  }

  /* ── Scanner ── */
  return (
    <View style={s.container}>
      <CameraView
        style={StyleSheet.absoluteFillObject}
        facing="back"
        barcodeScannerSettings={{
          barcodeTypes: ["qr", "code128", "code39", "ean13", "ean8", "upc_a"],
        }}
        onBarcodeScanned={scanned ? undefined : handleBarcodeScanned}
        onMountError={(e: any) => {
          setError(e?.message || "Failed to start camera");
        }}
      />

      {/* Top bar */}
      <View style={s.topBar}>
        <TouchableOpacity style={s.topBtn} onPress={() => router.back()}>
          <Text style={s.topBtnText}>Back</Text>
        </TouchableOpacity>
        <Text style={s.topTitle}>Scan Asset</Text>
        <View style={s.topBarActions}>
          <TouchableOpacity style={s.topBtn} onPress={() => setShowReaderModal(true)} disabled={rfidBusy}>
            <Text style={s.topBtnText}>Reader</Text>
          </TouchableOpacity>
          <TouchableOpacity style={s.topBtn} onPress={startRfidScan} disabled={rfidBusy}>
            <Text style={s.topBtnText}>{rfidBusy ? "Reading" : "RFID"}</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={s.topBtn}
            onPress={() => setShowManualEntry(true)}
          >
            <Text style={s.topBtnText}>Type</Text>
          </TouchableOpacity>
        </View>
      </View>

      {/* Center guide */}
      <View style={s.guideContainer}>
        <View style={s.guide}>
          <View style={[s.corner, { top: 0, left: 0, borderTopWidth: 3, borderLeftWidth: 3 }]} />
          <View style={[s.corner, { top: 0, right: 0, borderTopWidth: 3, borderRightWidth: 3 }]} />
          <View style={[s.corner, { bottom: 0, left: 0, borderBottomWidth: 3, borderLeftWidth: 3 }]} />
          <View style={[s.corner, { bottom: 0, right: 0, borderBottomWidth: 3, borderRightWidth: 3 }]} />
        </View>
        <Text style={s.guideText}>Point at QR code or barcode, or tap RFID</Text>
        <Text style={s.readerHint}>
          Reader: {availableReaders.find((reader) => reader.id === selectedReaderId)?.name ?? "Not selected"}
        </Text>
        {lastRfidValue ? <Text style={s.rfidHint}>Last RFID: {lastRfidValue}</Text> : null}
      </View>

      {/* Bottom */}
      {scanned && (
        <View style={s.bottomBar}>
          <TouchableOpacity
            style={s.btn}
            onPress={() => {
              setScanned(false);
              processingRef.current = false;
            }}
          >
            <Text style={s.btnText}>Scan Again</Text>
          </TouchableOpacity>
        </View>
      )}

      <Modal
        visible={showReaderModal}
        transparent
        animationType="fade"
        onRequestClose={() => setShowReaderModal(false)}
      >
        <View style={s.modalOverlay}>
          <View style={s.modalCard}>
            <Text style={s.modalTitle}>Select RFID Reader</Text>
            <Text style={s.modalSub}>Choose the adapter for your hardware.</Text>
            {availableReaders.map((reader) => (
              <TouchableOpacity
                key={reader.id}
                style={[
                  s.readerRow,
                  reader.id === selectedReaderId && s.readerRowActive,
                ]}
                onPress={() => {
                  void onSelectReader(reader.id);
                }}
              >
                <View style={{ flex: 1 }}>
                  <Text style={s.readerName}>{reader.name}</Text>
                  <Text style={s.readerMeta}>{reader.manufacturer} · {reader.transport}</Text>
                </View>
                <Text style={s.readerSelect}>{reader.id === selectedReaderId ? "Selected" : "Use"}</Text>
              </TouchableOpacity>
            ))}
            <TouchableOpacity style={s.modalCloseBtn} onPress={() => setShowReaderModal(false)}>
              <Text style={s.modalCloseText}>Close</Text>
            </TouchableOpacity>
          </View>
        </View>
      </Modal>
    </View>
  );
}

const s = StyleSheet.create({
  container: { flex: 1, backgroundColor: "#000" },
  centerContainer: {
    flex: 1,
    backgroundColor: "#F3F4F6",
    justifyContent: "center",
    alignItems: "center",
    padding: 24,
  },
  title: {
    fontSize: 20,
    fontWeight: "700",
    color: "#111827",
    marginBottom: 8,
    textAlign: "center",
  },
  subtitle: {
    fontSize: 14,
    color: "#6B7280",
    textAlign: "center",
    marginBottom: 24,
    lineHeight: 20,
  },
  btn: {
    backgroundColor: "#6366F1",
    paddingHorizontal: 32,
    paddingVertical: 14,
    borderRadius: 12,
    marginBottom: 12,
    minWidth: 200,
    alignItems: "center",
  },
  secondaryBtn: {
    backgroundColor: "#FFFFFF",
    borderWidth: 1.5,
    borderColor: "#D1D5DB",
    paddingHorizontal: 24,
    paddingVertical: 14,
    borderRadius: 12,
    marginBottom: 12,
    minWidth: 200,
    alignItems: "center",
  },
  btnText: { color: "#FFF", fontSize: 16, fontWeight: "700" },
  secondaryBtnText: { color: "#111827", fontSize: 16, fontWeight: "700" },
  linkText: { color: "#6B7280", fontSize: 14, fontWeight: "600", marginTop: 8 },

  card: {
    backgroundColor: "#FFF",
    borderRadius: 20,
    padding: 28,
    width: "100%",
    maxWidth: 340,
    alignItems: "center",
  },
  input: {
    backgroundColor: "#F9FAFB",
    borderWidth: 1.5,
    borderColor: "#E5E7EB",
    borderRadius: 12,
    paddingHorizontal: 16,
    paddingVertical: 14,
    fontSize: 17,
    fontWeight: "600",
    color: "#111827",
    letterSpacing: 0.5,
    marginBottom: 16,
    width: "100%",
  },
  toggleRow: {
    flexDirection: "row",
    backgroundColor: "#F3F4F6",
    borderRadius: 10,
    padding: 3,
    marginBottom: 16,
    width: "100%",
  },
  toggleBtn: {
    flex: 1,
    paddingVertical: 8,
    borderRadius: 8,
    alignItems: "center",
  },
  toggleBtnActive: {
    backgroundColor: "#6366F1",
  },
  toggleBtnText: {
    fontSize: 14,
    fontWeight: "600",
    color: "#6B7280",
  },
  toggleBtnTextActive: {
    color: "#FFF",
  },

  topBar: {
    position: "absolute",
    top: 0,
    left: 0,
    right: 0,
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingTop: Platform.OS === "ios" ? 56 : 44,
    paddingHorizontal: 16,
    paddingBottom: 12,
    backgroundColor: "rgba(0,0,0,0.5)",
  },
  topBarActions: {
    flexDirection: "row",
    gap: 8,
  },
  topBtn: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: "rgba(255,255,255,0.2)",
  },
  topBtnText: { color: "#FFF", fontSize: 14, fontWeight: "600" },
  topTitle: { color: "#FFF", fontSize: 17, fontWeight: "700" },

  guideContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  guide: { width: 240, height: 240, position: "relative" },
  corner: {
    position: "absolute",
    width: 28,
    height: 28,
    borderColor: "#6366F1",
  },
  guideText: {
    color: "#FFF",
    fontSize: 14,
    fontWeight: "500",
    marginTop: 16,
    textAlign: "center",
  },
  readerHint: {
    color: "#E5E7EB",
    fontSize: 12,
    marginTop: 8,
    textAlign: "center",
    paddingHorizontal: 20,
  },
  rfidHint: {
    color: "#E5E7EB",
    fontSize: 13,
    fontWeight: "600",
    marginTop: 10,
    textAlign: "center",
    paddingHorizontal: 24,
  },
  modalOverlay: {
    flex: 1,
    backgroundColor: "rgba(0,0,0,0.45)",
    justifyContent: "center",
    alignItems: "center",
    padding: 18,
  },
  modalCard: {
    width: "100%",
    maxWidth: 420,
    borderRadius: 16,
    backgroundColor: "#FFFFFF",
    padding: 18,
  },
  modalTitle: {
    fontSize: 18,
    fontWeight: "800",
    color: "#111827",
  },
  modalSub: {
    marginTop: 4,
    marginBottom: 14,
    fontSize: 13,
    color: "#6B7280",
  },
  readerRow: {
    flexDirection: "row",
    alignItems: "center",
    gap: 12,
    borderWidth: 1,
    borderColor: "#E5E7EB",
    borderRadius: 10,
    paddingHorizontal: 12,
    paddingVertical: 10,
    marginBottom: 8,
  },
  readerRowActive: {
    borderColor: "#6366F1",
    backgroundColor: "#EEF2FF",
  },
  readerName: {
    fontSize: 14,
    fontWeight: "700",
    color: "#111827",
  },
  readerMeta: {
    fontSize: 12,
    color: "#6B7280",
    marginTop: 2,
  },
  readerSelect: {
    fontSize: 12,
    fontWeight: "700",
    color: "#4338CA",
  },
  modalCloseBtn: {
    marginTop: 10,
    alignSelf: "flex-end",
    paddingHorizontal: 12,
    paddingVertical: 8,
    borderRadius: 8,
    backgroundColor: "#F3F4F6",
  },
  modalCloseText: {
    fontSize: 13,
    fontWeight: "700",
    color: "#111827",
  },

  bottomBar: {
    position: "absolute",
    bottom: 0,
    left: 0,
    right: 0,
    alignItems: "center",
    paddingVertical: 24,
    backgroundColor: "rgba(0,0,0,0.5)",
  },
});

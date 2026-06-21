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
} from "react-native";
import { Camera, CameraView, useCameraPermissions } from "expo-camera";
import { router } from "expo-router";
import { lookupAssetByRfidTag } from "../../src/services/asset-api";

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

/* ─── Exported screen ─── */
export default function ScanAssetScreen() {
  const [permission, requestPermission] = useCameraPermissions();
  const [scanned, setScanned] = useState(false);
  const [showManualEntry, setShowManualEntry] = useState(false);
  const [manualValue, setManualValue] = useState("");
  const [searchMode, setSearchMode] = useState<"tag" | "id" | "rfid">("tag");
  const [cameraReady, setCameraReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const processingRef = useRef(false);

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
      lookupAssetByRfidTag(value)
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
        <TouchableOpacity
          style={s.topBtn}
          onPress={() => setShowManualEntry(true)}
        >
          <Text style={s.topBtnText}>Type</Text>
        </TouchableOpacity>
      </View>

      {/* Center guide */}
      <View style={s.guideContainer}>
        <View style={s.guide}>
          <View style={[s.corner, { top: 0, left: 0, borderTopWidth: 3, borderLeftWidth: 3 }]} />
          <View style={[s.corner, { top: 0, right: 0, borderTopWidth: 3, borderRightWidth: 3 }]} />
          <View style={[s.corner, { bottom: 0, left: 0, borderBottomWidth: 3, borderLeftWidth: 3 }]} />
          <View style={[s.corner, { bottom: 0, right: 0, borderBottomWidth: 3, borderRightWidth: 3 }]} />
        </View>
        <Text style={s.guideText}>Point at QR code or barcode</Text>
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
  btnText: { color: "#FFF", fontSize: 16, fontWeight: "700" },
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

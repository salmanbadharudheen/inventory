import React, { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { ActivityIndicator, Alert, ScrollView, StyleSheet, Text, TextInput, TouchableOpacity, View } from "react-native";
import { router, useLocalSearchParams } from "expo-router";
import { lookupAssetByRfidTag } from "../../src/services/asset-api";
import { rfidManager } from "../../src/rfid";
import type { AssetDetail } from "../../src/types/api";
import type { StandardRfidRead } from "../../src/rfid";

const C = {
  bg: "#F3F4F6",
  card: "#FFFFFF",
  primary: "#4F46E5",
  primarySoft: "#EEF2FF",
  success: "#059669",
  successSoft: "#ECFDF5",
  warning: "#D97706",
  warningSoft: "#FFFBEB",
  danger: "#DC2626",
  dangerSoft: "#FEF2F2",
  text: "#111827",
  sub: "#6B7280",
  border: "#E5E7EB",
};

function normalizeEpc(value: string): string {
  return (value || "").trim().replace(/[\s.,;:!"'`]+$/g, "").replace(/[\s:-]+/g, "").toUpperCase();
}

export default function RoomInventoryScreen() {
  const params = useLocalSearchParams<{ room?: string }>();
  const [room, setRoom] = useState(Array.isArray(params.room) ? params.room[0] : params.room ?? "");
  const [readerName, setReaderName] = useState<string>(rfidManager.getSelectedReader()?.name ?? "Not selected");
  const [supported, setSupported] = useState<boolean | null>(null);
  const [scanning, setScanning] = useState(false);
  const [loadingScan, setLoadingScan] = useState(false);
  const [reads, setReads] = useState<StandardRfidRead[]>([]);
  const [matchedAssets, setMatchedAssets] = useState<AssetDetail[]>([]);
  const [unknownEpcs, setUnknownEpcs] = useState<string[]>([]);
  const [currentStatus, setCurrentStatus] = useState<string>("Idle");
  const seenEpcsRef = useRef(new Set<string>());
  const pendingLookupRef = useRef(new Set<string>());
  const scanUnsubscribeRef = useRef<(() => void) | null>(null);

  const clearScanSubscription = useCallback(() => {
    scanUnsubscribeRef.current?.();
    scanUnsubscribeRef.current = null;
  }, []);

  useEffect(() => {
    let mounted = true;

    (async () => {
      try {
        const isSupported = await rfidManager.isSelectedReaderSupported();
        if (!mounted) return;
        setSupported(isSupported);
        setReaderName(rfidManager.getSelectedReader()?.name ?? "Not selected");
      } catch (error: any) {
        if (mounted) {
          setSupported(false);
          setCurrentStatus(error?.message ?? "Reader unavailable");
        }
      }
    })();

    return () => {
      mounted = false;
      clearScanSubscription();
      rfidManager.stopScan().catch(() => undefined);
      rfidManager.disconnect().catch(() => undefined);
    };
  }, [clearScanSubscription]);

  const roomLabel = useMemo(() => room.trim() || "All rooms", [room]);

  const lookupAndStore = useCallback(async (epc: string) => {
    if (pendingLookupRef.current.has(epc)) return;
    pendingLookupRef.current.add(epc);

    try {
      const asset = await lookupAssetByRfidTag(epc);
      setMatchedAssets((prev) => (prev.some((item) => item.id === asset.id) ? prev : [asset, ...prev]));
      setCurrentStatus(`Matched ${epc}`);
    } catch {
      setUnknownEpcs((prev) => (prev.includes(epc) ? prev : [epc, ...prev]));
      setCurrentStatus(`Unknown RFID Tag: ${epc}`);
    } finally {
      pendingLookupRef.current.delete(epc);
    }
  }, []);

  const startScan = useCallback(async () => {
    if (loadingScan || scanning) return;
    if (supported === false) {
      Alert.alert("RFID Reader not available", "The selected reader is not supported in this build.");
      return;
    }

    setLoadingScan(true);
    setCurrentStatus("Connecting to reader...");

    try {
      await rfidManager.connect();
      clearScanSubscription();
      scanUnsubscribeRef.current = rfidManager.onRead((read) => {
        const epc = normalizeEpc(read.epc);
        if (!epc || seenEpcsRef.current.has(epc)) return;
        seenEpcsRef.current.add(epc);
        setReads((prev) => [read, ...prev]);
        void lookupAndStore(epc);
      });
      await rfidManager.startScan();
      setScanning(true);
      setCurrentStatus("Scanning room for EPCs...");
    } catch (error: any) {
      Alert.alert("Scan failed", error?.message ?? "Unable to start RFID scan.");
      setCurrentStatus(error?.message ?? "Scan failed");
      clearScanSubscription();
      await rfidManager.stopScan().catch(() => undefined);
      await rfidManager.disconnect().catch(() => undefined);
      setScanning(false);
    } finally {
      setLoadingScan(false);
    }
  }, [clearScanSubscription, loadingScan, lookupAndStore, scanning, supported]);

  const stopScan = useCallback(async () => {
    clearScanSubscription();
    await rfidManager.stopScan().catch(() => undefined);
    await rfidManager.disconnect().catch(() => undefined);
    setScanning(false);
    setCurrentStatus("Scan stopped");
  }, [clearScanSubscription]);

  const clearResults = useCallback(() => {
    seenEpcsRef.current.clear();
    pendingLookupRef.current.clear();
    setReads([]);
    setMatchedAssets([]);
    setUnknownEpcs([]);
    setCurrentStatus("Cleared");
  }, []);

  return (
    <View style={styles.screen}>
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <View style={styles.headerCard}>
          <Text style={styles.title}>Room Inventory Scan</Text>
          <Text style={styles.subtitle}>Reader: {readerName}</Text>
          <Text style={styles.subtitle}>Room: {roomLabel}</Text>
          <Text style={styles.status}>{currentStatus}</Text>

          <View style={styles.roomRow}>
            <TextInput
              style={styles.roomInput}
              value={room}
              onChangeText={setRoom}
              placeholder="Enter room / location label"
              placeholderTextColor={C.sub}
            />
            <TouchableOpacity style={styles.smallBtn} onPress={() => router.setParams({ room })}>
              <Text style={styles.smallBtnText}>Save</Text>
            </TouchableOpacity>
          </View>

          <View style={styles.actionsRow}>
            <TouchableOpacity style={[styles.primaryBtn, scanning && styles.disabledBtn]} onPress={startScan} disabled={scanning || loadingScan}>
              {loadingScan ? <ActivityIndicator color="#FFF" /> : <Text style={styles.primaryBtnText}>{scanning ? "Scanning" : "Start Scan"}</Text>}
            </TouchableOpacity>
            <TouchableOpacity style={styles.secondaryBtn} onPress={stopScan}>
              <Text style={styles.secondaryBtnText}>Stop</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.secondaryBtn} onPress={clearResults}>
              <Text style={styles.secondaryBtnText}>Clear</Text>
            </TouchableOpacity>
          </View>
        </View>

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Matched Assets</Text>
          {matchedAssets.length === 0 ? (
            <Text style={styles.emptyText}>No assets matched yet.</Text>
          ) : matchedAssets.map((asset) => (
            <TouchableOpacity key={asset.id} style={styles.assetRow} onPress={() => router.push({ pathname: "/(app)/asset-detail", params: { asset_id: asset.id, from_scan: "1" } })}>
              <View style={{ flex: 1 }}>
                <Text style={styles.assetName}>{asset.name}</Text>
                <Text style={styles.assetMeta}>{asset.asset_code || asset.asset_tag}</Text>
                <Text style={styles.assetMeta}>{asset.site_name || "No site"} · {asset.building_name || "No building"}</Text>
              </View>
              <View style={[styles.badge, { backgroundColor: C.successSoft }]}>
                <Text style={[styles.badgeText, { color: C.success }]}>Matched</Text>
              </View>
            </TouchableOpacity>
          ))}
        </View>

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Unknown EPCs</Text>
          {unknownEpcs.length === 0 ? (
            <Text style={styles.emptyText}>No unknown tags yet.</Text>
          ) : unknownEpcs.map((epc) => (
            <View key={epc} style={styles.assetRow}>
              <View style={{ flex: 1 }}>
                <Text style={styles.assetName}>{epc}</Text>
                <Text style={styles.assetMeta}>Not registered</Text>
              </View>
              <View style={[styles.badge, { backgroundColor: C.dangerSoft }]}>
                <Text style={[styles.badgeText, { color: C.danger }]}>Unknown</Text>
              </View>
            </View>
          ))}
        </View>

        <View style={styles.card}>
          <Text style={styles.sectionTitle}>Raw Reads</Text>
          {reads.length === 0 ? (
            <Text style={styles.emptyText}>No EPC reads yet.</Text>
          ) : reads.map((read) => (
            <View key={`${read.readerId}-${read.timestamp}-${read.epc}`} style={styles.readRow}>
              <Text style={styles.readEpc}>{read.epc}</Text>
              <Text style={styles.readMeta}>{read.manufacturer} · {new Date(read.timestamp).toLocaleTimeString()}</Text>
            </View>
          ))}
        </View>
      </ScrollView>
    </View>
  );
}

const styles = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.bg },
  content: { padding: 16, paddingBottom: 40 },
  headerCard: { backgroundColor: C.card, borderRadius: 18, padding: 18, marginBottom: 12, borderWidth: 1, borderColor: C.border },
  card: { backgroundColor: C.card, borderRadius: 18, padding: 16, marginBottom: 12, borderWidth: 1, borderColor: C.border },
  title: { fontSize: 22, fontWeight: "800", color: C.text },
  subtitle: { marginTop: 4, color: C.sub, fontSize: 13 },
  status: { marginTop: 10, color: C.primary, fontSize: 13, fontWeight: "700" },
  roomRow: { flexDirection: "row", gap: 8, marginTop: 14 },
  roomInput: { flex: 1, backgroundColor: "#F9FAFB", borderWidth: 1, borderColor: C.border, borderRadius: 12, paddingHorizontal: 12, paddingVertical: 10, color: C.text },
  smallBtn: { backgroundColor: C.primarySoft, borderRadius: 12, justifyContent: "center", paddingHorizontal: 14 },
  smallBtnText: { color: C.primary, fontWeight: "700" },
  actionsRow: { flexDirection: "row", gap: 8, marginTop: 14, flexWrap: "wrap" },
  primaryBtn: { flexGrow: 1, backgroundColor: C.primary, borderRadius: 12, paddingVertical: 12, paddingHorizontal: 16, alignItems: "center", minWidth: 120 },
  disabledBtn: { opacity: 0.7 },
  primaryBtnText: { color: "#FFF", fontWeight: "800" },
  secondaryBtn: { backgroundColor: "#FFF", borderWidth: 1, borderColor: C.border, borderRadius: 12, paddingVertical: 12, paddingHorizontal: 16, alignItems: "center" },
  secondaryBtnText: { color: C.text, fontWeight: "700" },
  sectionTitle: { fontSize: 16, fontWeight: "800", color: C.text, marginBottom: 12 },
  emptyText: { color: C.sub, fontSize: 13 },
  assetRow: { flexDirection: "row", gap: 10, alignItems: "center", paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: C.border },
  assetName: { color: C.text, fontSize: 14, fontWeight: "700" },
  assetMeta: { color: C.sub, fontSize: 12, marginTop: 2 },
  badge: { paddingHorizontal: 10, paddingVertical: 6, borderRadius: 999 },
  badgeText: { fontSize: 12, fontWeight: "800" },
  readRow: { paddingVertical: 10, borderBottomWidth: 1, borderBottomColor: C.border },
  readEpc: { fontSize: 14, fontWeight: "700", color: C.text },
  readMeta: { fontSize: 12, color: C.sub, marginTop: 4 },
});

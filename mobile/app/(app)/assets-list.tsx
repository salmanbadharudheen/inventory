import React, { useCallback, useEffect, useState } from "react";
import {
  ActivityIndicator,
  RefreshControl,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from "react-native";
import { router } from "expo-router";
import { listAssets } from "../../src/services/asset-api";
import type { AssetDetail } from "../../src/types/api";

export default function AssetsListScreen() {
  const [assets, setAssets] = useState<AssetDetail[]>([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [query, setQuery] = useState("");

  const load = useCallback(async (silent = false) => {
    try {
      if (!silent) setLoading(true);
      setError(null);
      const data = await listAssets({ page: 1, search: query.trim() || undefined });
      setAssets(data.results || []);
    } catch (e: any) {
      setError(e?.message ?? "Failed to load assets");
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [query]);

  useEffect(() => {
    void load();
  }, [load]);

  const onRefresh = () => {
    setRefreshing(true);
    void load(true);
  };

  const onSearch = () => {
    void load();
  };

  if (loading && assets.length === 0) {
    return (
      <View style={s.center}>
        <ActivityIndicator size="large" color="#4F46E5" />
        <Text style={s.sub}>Loading assets...</Text>
      </View>
    );
  }

  if (error && assets.length === 0) {
    return (
      <View style={s.center}>
        <Text style={s.errorTitle}>Unable to load assets</Text>
        <Text style={s.sub}>{error}</Text>
        <TouchableOpacity style={s.primaryBtn} onPress={() => void load()}>
          <Text style={s.primaryBtnText}>Retry</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={s.screen}>
      <View style={s.searchRow}>
        <TextInput
          style={s.searchInput}
          value={query}
          onChangeText={setQuery}
          placeholder="Search by name, tag, RFID..."
          placeholderTextColor="#94A3B8"
          returnKeyType="search"
          onSubmitEditing={onSearch}
        />
        <TouchableOpacity style={s.searchBtn} onPress={onSearch}>
          <Text style={s.searchBtnText}>Search</Text>
        </TouchableOpacity>
      </View>

      <ScrollView
        contentContainerStyle={{ paddingBottom: 24 }}
        refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}
        showsVerticalScrollIndicator={false}
      >
        {assets.length === 0 ? (
          <View style={s.emptyCard}>
            <Text style={s.emptyTitle}>No assets found</Text>
            <Text style={s.sub}>Try another search value.</Text>
          </View>
        ) : (
          assets.map((asset) => (
            <TouchableOpacity
              key={asset.id}
              style={s.assetCard}
              activeOpacity={0.75}
              onPress={() => {
                router.push({
                  pathname: "/(app)/asset-detail",
                  params: { asset_id: asset.id },
                });
              }}
            >
              <Text style={s.assetName} numberOfLines={1}>{asset.name}</Text>
              <Text style={s.assetMeta} numberOfLines={1}>Tag: {asset.asset_tag}</Text>
              <Text style={s.assetMeta} numberOfLines={1}>RFID: {asset.rfid_tag || "Not assigned"}</Text>
            </TouchableOpacity>
          ))
        )}
      </ScrollView>
    </View>
  );
}

const s = StyleSheet.create({
  screen: {
    flex: 1,
    backgroundColor: "#F1F5F9",
    paddingHorizontal: 16,
    paddingTop: 14,
  },
  center: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
    paddingHorizontal: 20,
    backgroundColor: "#F1F5F9",
  },
  sub: {
    marginTop: 10,
    color: "#64748B",
    textAlign: "center",
  },
  errorTitle: {
    fontSize: 18,
    fontWeight: "700",
    color: "#0F172A",
    textAlign: "center",
  },
  primaryBtn: {
    marginTop: 14,
    backgroundColor: "#4F46E5",
    paddingHorizontal: 18,
    paddingVertical: 11,
    borderRadius: 10,
  },
  primaryBtnText: {
    color: "#FFF",
    fontWeight: "700",
  },
  searchRow: {
    flexDirection: "row",
    gap: 8,
    marginBottom: 12,
  },
  searchInput: {
    flex: 1,
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E2E8F0",
    borderRadius: 12,
    paddingHorizontal: 14,
    paddingVertical: 12,
    color: "#0F172A",
  },
  searchBtn: {
    backgroundColor: "#4F46E5",
    borderRadius: 12,
    justifyContent: "center",
    paddingHorizontal: 16,
  },
  searchBtnText: {
    color: "#FFF",
    fontWeight: "700",
  },
  emptyCard: {
    backgroundColor: "#FFFFFF",
    borderRadius: 14,
    borderWidth: 1,
    borderColor: "#E2E8F0",
    padding: 18,
  },
  emptyTitle: {
    fontSize: 16,
    fontWeight: "700",
    color: "#0F172A",
  },
  assetCard: {
    backgroundColor: "#FFFFFF",
    borderWidth: 1,
    borderColor: "#E2E8F0",
    borderRadius: 14,
    padding: 14,
    marginBottom: 10,
  },
  assetName: {
    fontSize: 15,
    fontWeight: "700",
    color: "#0F172A",
    marginBottom: 4,
  },
  assetMeta: {
    fontSize: 12,
    color: "#64748B",
  },
});

import React, { useCallback, useEffect, useMemo, useState } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  ActivityIndicator,
  Alert,
  Platform,
  KeyboardAvoidingView,
} from "react-native";
import { router } from "expo-router";
import {
  createAsset,
  getCategories,
  getSubCategories,
  getGroups,
  getSubGroups,
  getCompanies,
  getRegions,
  getSites,
  getBuildings,
  getFloors,
  getDepartments,
} from "../../src/services/asset-api";
import type {
  AssetCreatePayload,
  CategoryItem,
  LookupItem,
  AssetCondition,
  AssetType,
} from "../../src/types/api";

/* ───── colours (shared w/ dashboard) ───── */
const C = {
  primary: "#6366F1",
  primaryLight: "#EEF2FF",
  success: "#10B981",
  danger: "#EF4444",
  bg: "#F3F4F6",
  white: "#FFFFFF",
  text: "#111827",
  muted: "#6B7280",
  border: "#E5E7EB",
  inputBg: "#F9FAFB",
};

/* ───── static option lists ───── */
const CONDITIONS: { value: AssetCondition; label: string }[] = [
  { value: "NEW", label: "New" },
  { value: "USED", label: "Used" },
  { value: "DAMAGED", label: "Damaged" },
  { value: "UNDER_REPAIR", label: "Under Repair" },
];

const ASSET_TYPES: { value: AssetType; label: string }[] = [
  { value: "TAGGABLE", label: "Taggable" },
  { value: "BUILDING_IMPROVEMENTS", label: "Building Improvements" },
  { value: "NTA", label: "NTA" },
  { value: "CAPEX", label: "CAPEX" },
];

/* ───── helpers ───── */
type Section = "basic" | "classification" | "location" | "financial" | "notes";

const SECTIONS: { key: Section; label: string; icon: string }[] = [
  { key: "basic", label: "Basic Info", icon: "📦" },
  { key: "classification", label: "Classification", icon: "🏷️" },
  { key: "location", label: "Location", icon: "📍" },
  { key: "financial", label: "Financial", icon: "💰" },
  { key: "notes", label: "Notes", icon: "📝" },
];

/* ───── main component ───── */
export default function AddAssetScreen() {
  /* ── form state ── */
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [shortDesc, setShortDesc] = useState("");
  const [serialNumber, setSerialNumber] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [condition, setCondition] = useState<AssetCondition>("NEW");
  const [assetType, setAssetType] = useState<AssetType>("TAGGABLE");
  const [brandText, setBrandText] = useState("");
  const [modelText, setModelText] = useState("");

  // FK pickers
  const [categoryId, setCategoryId] = useState<number | null>(null);
  const [subCategoryId, setSubCategoryId] = useState<number | null>(null);
  const [groupId, setGroupId] = useState<number | null>(null);
  const [subGroupId, setSubGroupId] = useState<number | null>(null);
  const [companyId, setCompanyId] = useState<number | null>(null);
  const [departmentId, setDepartmentId] = useState<number | null>(null);
  const [regionId, setRegionId] = useState<number | null>(null);
  const [siteId, setSiteId] = useState<number | null>(null);
  const [buildingId, setBuildingId] = useState<number | null>(null);
  const [floorId, setFloorId] = useState<number | null>(null);

  // Financial
  const [purchaseDate, setPurchaseDate] = useState("");
  const [purchasePrice, setPurchasePrice] = useState("");
  const [currency, setCurrency] = useState("AED");
  const [invoiceNumber, setInvoiceNumber] = useState("");
  const [poNumber, setPoNumber] = useState("");

  // Notes
  const [notes, setNotes] = useState("");

  /* ── lookup data ── */
  const [categories, setCategories] = useState<CategoryItem[]>([]);
  const [subCategories, setSubCategories] = useState<LookupItem[]>([]);
  const [groups, setGroups] = useState<LookupItem[]>([]);
  const [subGroups, setSubGroups] = useState<LookupItem[]>([]);
  const [companies, setCompanies] = useState<LookupItem[]>([]);
  const [departments, setDepartments] = useState<LookupItem[]>([]);
  const [regions, setRegions] = useState<LookupItem[]>([]);
  const [sites, setSites] = useState<LookupItem[]>([]);
  const [buildings, setBuildings] = useState<LookupItem[]>([]);
  const [floors, setFloors] = useState<LookupItem[]>([]);

  /* ── UI state ── */
  const [activeSection, setActiveSection] = useState<Section>("basic");
  const [submitting, setSubmitting] = useState(false);
  const [loadingLookups, setLoadingLookups] = useState(true);

  /* ── load initial lookups ── */
  useEffect(() => {
    (async () => {
      try {
        const [cats, grps, comps, regs, depts] = await Promise.all([
          getCategories(),
          getGroups(),
          getCompanies(),
          getRegions(),
          getDepartments(),
        ]);
        setCategories(cats);
        setGroups(grps);
        setCompanies(comps);
        setRegions(regs);
        setDepartments(depts);
      } finally {
        setLoadingLookups(false);
      }
    })();
  }, []);

  /* ── cascading lookups ── */
  useEffect(() => {
    setSubCategoryId(null);
    if (categoryId) getSubCategories(categoryId).then(setSubCategories);
    else setSubCategories([]);
  }, [categoryId]);

  useEffect(() => {
    setSubGroupId(null);
    if (groupId) getSubGroups(groupId).then(setSubGroups);
    else setSubGroups([]);
  }, [groupId]);

  useEffect(() => {
    setSiteId(null);
    setBuildingId(null);
    setFloorId(null);
    if (regionId) getSites(regionId).then(setSites);
    else setSites([]);
  }, [regionId]);

  useEffect(() => {
    setBuildingId(null);
    setFloorId(null);
    if (siteId) getBuildings(siteId).then(setBuildings);
    else setBuildings([]);
  }, [siteId]);

  useEffect(() => {
    setFloorId(null);
    if (buildingId) getFloors(buildingId).then(setFloors);
    else setFloors([]);
  }, [buildingId]);

  /* ── build payload ── */
  const buildPayload = useCallback((): AssetCreatePayload => {
    const p: AssetCreatePayload = {
      name: name.trim(),
      category: categoryId!,
      condition,
      asset_type: assetType,
    };
    if (description.trim()) p.description = description.trim();
    if (shortDesc.trim()) p.short_description = shortDesc.trim();
    if (serialNumber.trim()) p.serial_number = serialNumber.trim();
    const qty = parseInt(quantity, 10);
    if (qty > 1) p.quantity = qty;
    if (brandText.trim()) p.brand = brandText.trim();
    if (modelText.trim()) p.model = modelText.trim();
    if (subCategoryId) p.sub_category = subCategoryId;
    if (groupId) p.group = groupId;
    if (subGroupId) p.sub_group = subGroupId;
    if (companyId) p.company = companyId;
    if (departmentId) p.department = departmentId;
    if (regionId) p.region = regionId;
    if (siteId) p.site = siteId;
    if (buildingId) p.building = buildingId;
    if (floorId) p.floor = floorId;
    if (purchaseDate.trim()) p.purchase_date = purchaseDate.trim();
    if (purchasePrice.trim()) p.purchase_price = purchasePrice.trim();
    if (currency.trim()) p.currency = currency.trim();
    if (invoiceNumber.trim()) p.invoice_number = invoiceNumber.trim();
    if (poNumber.trim()) p.po_number = poNumber.trim();
    if (notes.trim()) p.notes = notes.trim();
    return p;
  }, [
    name, categoryId, condition, assetType, description, shortDesc,
    serialNumber, quantity, brandText, modelText, subCategoryId,
    groupId, subGroupId, companyId, departmentId, regionId,
    siteId, buildingId, floorId, purchaseDate, purchasePrice,
    currency, invoiceNumber, poNumber, notes,
  ]);

  /* ── submit ── */
  const handleSubmit = async () => {
    if (!name.trim()) {
      Alert.alert("Validation", "Asset name is required.");
      setActiveSection("basic");
      return;
    }
    if (!categoryId) {
      Alert.alert("Validation", "Category is required.");
      setActiveSection("basic");
      return;
    }

    setSubmitting(true);
    try {
      const res = await createAsset(buildPayload());
      Alert.alert("Success", res.detail, [
        { text: "OK", onPress: () => router.back() },
      ]);
    } catch (e: any) {
      Alert.alert("Error", e.message ?? "Failed to create asset.");
    } finally {
      setSubmitting(false);
    }
  };

  /* ── validation badge ── */
  const basicValid = !!(name.trim() && categoryId);

  /* ── loading state ── */
  if (loadingLookups) {
    return (
      <View style={[s.center, { flex: 1, backgroundColor: C.bg }]}>
        <ActivityIndicator size="large" color={C.primary} />
        <Text style={{ color: C.muted, marginTop: 12 }}>Loading form data…</Text>
      </View>
    );
  }

  /* ──────────── RENDER ──────────── */
  return (
    <KeyboardAvoidingView
      style={{ flex: 1 }}
      behavior={Platform.OS === "ios" ? "padding" : undefined}
    >
      <View style={s.screen}>
        {/* ── Section tabs ── */}
        <ScrollView
          horizontal
          showsHorizontalScrollIndicator={false}
          style={s.tabBar}
          contentContainerStyle={s.tabBarContent}
        >
          {SECTIONS.map((sec) => (
            <TouchableOpacity
              key={sec.key}
              style={[s.tab, activeSection === sec.key && s.tabActive]}
              onPress={() => setActiveSection(sec.key)}
            >
              <Text style={s.tabIcon}>{sec.icon}</Text>
              <Text
                style={[s.tabLabel, activeSection === sec.key && s.tabLabelActive]}
              >
                {sec.label}
              </Text>
              {sec.key === "basic" && !basicValid && (
                <View style={s.requiredDot} />
              )}
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* ── Form body ── */}
        <ScrollView
          style={s.body}
          contentContainerStyle={s.bodyContent}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          {activeSection === "basic" && (
            <>
              <Label text="Asset Name" required />
              <Input value={name} onChangeText={setName} placeholder="e.g. Dell Latitude 5520" />

              <Label text="Category" required />
              <Picker
                items={categories}
                selectedId={categoryId}
                onSelect={setCategoryId}
                placeholder="Select category"
              />

              {subCategories.length > 0 && (
                <>
                  <Label text="Sub-category" />
                  <Picker items={subCategories} selectedId={subCategoryId} onSelect={setSubCategoryId} placeholder="Select sub-category" />
                </>
              )}

              <Label text="Short Description" />
              <Input value={shortDesc} onChangeText={setShortDesc} placeholder="Brief summary" />

              <Label text="Description" />
              <Input
                value={description}
                onChangeText={setDescription}
                placeholder="Detailed description"
                multiline
                numberOfLines={3}
                style={{ minHeight: 70 }}
              />

              <Label text="Serial Number" />
              <Input value={serialNumber} onChangeText={setSerialNumber} placeholder="e.g. SN-12345" />

              <Label text="Quantity" />
              <Input
                value={quantity}
                onChangeText={setQuantity}
                placeholder="1"
                keyboardType="number-pad"
              />

              <Label text="Condition" />
              <ChipRow
                items={CONDITIONS}
                selected={condition}
                onSelect={(v) => setCondition(v as AssetCondition)}
              />

              <Label text="Asset Type" />
              <ChipRow
                items={ASSET_TYPES}
                selected={assetType}
                onSelect={(v) => setAssetType(v as AssetType)}
              />
            </>
          )}

          {activeSection === "classification" && (
            <>
              <Label text="Group" />
              <Picker items={groups} selectedId={groupId} onSelect={setGroupId} placeholder="Select group" />

              {subGroups.length > 0 && (
                <>
                  <Label text="Sub-group" />
                  <Picker items={subGroups} selectedId={subGroupId} onSelect={setSubGroupId} placeholder="Select sub-group" />
                </>
              )}

              <Label text="Company" />
              <Picker items={companies} selectedId={companyId} onSelect={setCompanyId} placeholder="Select company" />

              <Label text="Department" />
              <Picker items={departments} selectedId={departmentId} onSelect={setDepartmentId} placeholder="Select department" />

              <Label text="Brand" />
              <Input value={brandText} onChangeText={setBrandText} placeholder="e.g. Dell, HP, Apple" />

              <Label text="Model" />
              <Input value={modelText} onChangeText={setModelText} placeholder="e.g. Latitude 5520" />
            </>
          )}

          {activeSection === "location" && (
            <>
              <Label text="Region" />
              <Picker items={regions} selectedId={regionId} onSelect={setRegionId} placeholder="Select region" />

              {sites.length > 0 && (
                <>
                  <Label text="Site" />
                  <Picker items={sites} selectedId={siteId} onSelect={setSiteId} placeholder="Select site" />
                </>
              )}

              {buildings.length > 0 && (
                <>
                  <Label text="Building" />
                  <Picker items={buildings} selectedId={buildingId} onSelect={setBuildingId} placeholder="Select building" />
                </>
              )}

              {floors.length > 0 && (
                <>
                  <Label text="Floor" />
                  <Picker items={floors} selectedId={floorId} onSelect={setFloorId} placeholder="Select floor" />
                </>
              )}
            </>
          )}

          {activeSection === "financial" && (
            <>
              <Label text="Purchase Date" />
              <Input
                value={purchaseDate}
                onChangeText={setPurchaseDate}
                placeholder="YYYY-MM-DD"
                keyboardType="numbers-and-punctuation"
              />

              <Label text="Purchase Price" />
              <Input
                value={purchasePrice}
                onChangeText={setPurchasePrice}
                placeholder="0.00"
                keyboardType="decimal-pad"
              />

              <Label text="Currency" />
              <Input value={currency} onChangeText={setCurrency} placeholder="AED" />

              <Label text="Invoice Number" />
              <Input value={invoiceNumber} onChangeText={setInvoiceNumber} placeholder="INV-0001" />

              <Label text="PO Number" />
              <Input value={poNumber} onChangeText={setPoNumber} placeholder="PO-0001" />
            </>
          )}

          {activeSection === "notes" && (
            <>
              <Label text="Notes / Remarks" />
              <Input
                value={notes}
                onChangeText={setNotes}
                placeholder="Any additional notes..."
                multiline
                numberOfLines={6}
                style={{ minHeight: 120 }}
              />
            </>
          )}

          <View style={{ height: 100 }} />
        </ScrollView>

        {/* ── Submit bar ── */}
        <View style={s.submitBar}>
          <TouchableOpacity style={s.cancelBtn} onPress={() => router.back()}>
            <Text style={s.cancelText}>Cancel</Text>
          </TouchableOpacity>
          <TouchableOpacity
            style={[s.submitBtn, submitting && { opacity: 0.6 }]}
            onPress={handleSubmit}
            disabled={submitting}
          >
            {submitting ? (
              <ActivityIndicator color="#fff" size="small" />
            ) : (
              <Text style={s.submitText}>Create Asset</Text>
            )}
          </TouchableOpacity>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}

/* ───── reusable sub-components ───── */

function Label({ text, required }: { text: string; required?: boolean }) {
  return (
    <Text style={s.label}>
      {text}
      {required && <Text style={{ color: C.danger }}> *</Text>}
    </Text>
  );
}

function Input(props: React.ComponentProps<typeof TextInput> & { style?: any }) {
  const { style: extra, ...rest } = props;
  return (
    <TextInput
      style={[s.input, props.multiline && s.inputMultiline, extra]}
      placeholderTextColor={C.muted}
      {...rest}
    />
  );
}

function Picker({
  items,
  selectedId,
  onSelect,
  placeholder,
}: {
  items: { id: number; name: string }[];
  selectedId: number | null;
  onSelect: (id: number | null) => void;
  placeholder: string;
}) {
  const [open, setOpen] = useState(false);
  const [search, setSearch] = useState("");
  const selected = items.find((i) => i.id === selectedId);
  const filtered = useMemo(
    () =>
      search
        ? items.filter((i) => i.name.toLowerCase().includes(search.toLowerCase()))
        : items,
    [items, search]
  );

  return (
    <View>
      <TouchableOpacity style={s.pickerBtn} onPress={() => setOpen(!open)}>
        <Text style={selected ? s.pickerText : s.pickerPlaceholder}>
          {selected?.name ?? placeholder}
        </Text>
        <Text style={{ fontSize: 12, color: C.muted }}>{open ? "▲" : "▼"}</Text>
      </TouchableOpacity>

      {open && (
        <View style={s.dropdown}>
          {items.length > 5 && (
            <TextInput
              style={s.dropdownSearch}
              placeholder="Search…"
              placeholderTextColor={C.muted}
              value={search}
              onChangeText={setSearch}
              autoFocus
            />
          )}
          {selectedId && (
            <TouchableOpacity
              style={s.dropdownItem}
              onPress={() => { onSelect(null); setOpen(false); setSearch(""); }}
            >
              <Text style={[s.dropdownText, { color: C.danger }]}>✕  Clear</Text>
            </TouchableOpacity>
          )}
          <ScrollView style={{ maxHeight: 200 }} nestedScrollEnabled keyboardShouldPersistTaps="handled">
            {filtered.map((item) => (
              <TouchableOpacity
                key={item.id}
                style={[s.dropdownItem, item.id === selectedId && s.dropdownItemActive]}
                onPress={() => { onSelect(item.id); setOpen(false); setSearch(""); }}
              >
                <Text
                  style={[s.dropdownText, item.id === selectedId && { color: C.primary, fontWeight: "700" }]}
                  numberOfLines={1}
                >
                  {item.name}
                </Text>
              </TouchableOpacity>
            ))}
            {filtered.length === 0 && (
              <Text style={{ padding: 12, color: C.muted, textAlign: "center" }}>No results</Text>
            )}
          </ScrollView>
        </View>
      )}
    </View>
  );
}

function ChipRow({
  items,
  selected,
  onSelect,
}: {
  items: { value: string; label: string }[];
  selected: string;
  onSelect: (v: string) => void;
}) {
  return (
    <ScrollView horizontal showsHorizontalScrollIndicator={false} style={{ marginBottom: 12 }}>
      {items.map((item) => (
        <TouchableOpacity
          key={item.value}
          style={[s.chip, item.value === selected && s.chipActive]}
          onPress={() => onSelect(item.value)}
        >
          <Text style={[s.chipText, item.value === selected && s.chipTextActive]}>
            {item.label}
          </Text>
        </TouchableOpacity>
      ))}
    </ScrollView>
  );
}

/* ───── styles ───── */
const s = StyleSheet.create({
  screen: { flex: 1, backgroundColor: C.bg },
  center: { justifyContent: "center", alignItems: "center" },

  /* tab bar */
  tabBar: { backgroundColor: C.white, borderBottomWidth: 1, borderColor: C.border, flexGrow: 0 },
  tabBarContent: { paddingHorizontal: 8, gap: 4, paddingVertical: 8 },
  tab: {
    flexDirection: "row",
    alignItems: "center",
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: C.bg,
    gap: 6,
  },
  tabActive: { backgroundColor: C.primaryLight, borderColor: C.primary, borderWidth: 1 },
  tabIcon: { fontSize: 14 },
  tabLabel: { fontSize: 13, color: C.muted, fontWeight: "600" },
  tabLabelActive: { color: C.primary },
  requiredDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: C.danger,
    marginLeft: 2,
  },

  /* body */
  body: { flex: 1 },
  bodyContent: { padding: 16 },

  /* label */
  label: { fontSize: 13, fontWeight: "600", color: C.text, marginBottom: 6, marginTop: 14 },

  /* input */
  input: {
    backgroundColor: C.inputBg,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 12,
    fontSize: 15,
    color: C.text,
  },
  inputMultiline: { textAlignVertical: "top" },

  /* picker */
  pickerBtn: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    backgroundColor: C.inputBg,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 10,
    paddingHorizontal: 14,
    paddingVertical: 13,
  },
  pickerText: { fontSize: 15, color: C.text },
  pickerPlaceholder: { fontSize: 15, color: C.muted },

  /* dropdown */
  dropdown: {
    backgroundColor: C.white,
    borderWidth: 1,
    borderColor: C.border,
    borderRadius: 10,
    marginTop: 4,
    overflow: "hidden",
    elevation: 4,
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 8,
  },
  dropdownSearch: {
    borderBottomWidth: 1,
    borderColor: C.border,
    paddingHorizontal: 12,
    paddingVertical: 10,
    fontSize: 14,
    color: C.text,
  },
  dropdownItem: { paddingHorizontal: 14, paddingVertical: 12, borderBottomWidth: 0.5, borderColor: C.border },
  dropdownItemActive: { backgroundColor: C.primaryLight },
  dropdownText: { fontSize: 14, color: C.text },

  /* chips */
  chip: {
    paddingHorizontal: 14,
    paddingVertical: 8,
    borderRadius: 20,
    backgroundColor: C.inputBg,
    borderWidth: 1,
    borderColor: C.border,
    marginRight: 8,
  },
  chipActive: { backgroundColor: C.primaryLight, borderColor: C.primary },
  chipText: { fontSize: 13, color: C.muted, fontWeight: "600" },
  chipTextActive: { color: C.primary },

  /* submit bar */
  submitBar: {
    flexDirection: "row",
    padding: 16,
    paddingBottom: Platform.OS === "ios" ? 30 : 16,
    backgroundColor: C.white,
    borderTopWidth: 1,
    borderColor: C.border,
    gap: 12,
  },
  cancelBtn: {
    flex: 1,
    paddingVertical: 14,
    borderRadius: 12,
    borderWidth: 1,
    borderColor: C.border,
    alignItems: "center",
  },
  cancelText: { fontSize: 15, fontWeight: "700", color: C.muted },
  submitBtn: {
    flex: 2,
    paddingVertical: 14,
    borderRadius: 12,
    backgroundColor: C.primary,
    alignItems: "center",
    justifyContent: "center",
  },
  submitText: { fontSize: 15, fontWeight: "700", color: "#fff" },
});

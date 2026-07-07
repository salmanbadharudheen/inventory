import { Platform } from "react-native";
import NfcManager, { Ndef, NfcTech } from "react-native-nfc-manager";
import type { ReaderInfo, RfidReadListener, RfidReaderAdapter } from "../types";
import { normalizeEpc } from "../utils/normalize";

function decodeNdefPayload(ndefMessage: Array<{ tnf: number; type: number[] | string; payload: number[] }> | undefined): string {
  if (!ndefMessage?.length) return "";

  for (const record of ndefMessage) {
    const recordType = Array.isArray(record.type)
      ? String.fromCharCode(...record.type)
      : record.type;
    const payload = new Uint8Array(record.payload || []);

    if (record.tnf === Ndef.TNF_WELL_KNOWN && recordType === Ndef.RTD_TEXT) {
      const textValue = Ndef.text.decodePayload(payload).trim();
      if (textValue) return textValue;
    }

    if (record.tnf === Ndef.TNF_WELL_KNOWN && recordType === Ndef.RTD_URI) {
      const uriValue = Ndef.uri.decodePayload(payload).trim();
      if (uriValue) return uriValue;
    }

    const fallbackValue = Ndef.util.bytesToString(record.payload || []).trim();
    if (fallbackValue) return fallbackValue;
  }

  return "";
}

function extractEpcFromTag(tag: {
  id?: string;
  identifier?: string;
  serialNumber?: string;
  ndefMessage?: Array<{ tnf: number; type: number[] | string; payload: number[] }>;
} | null): string {
  const candidates: Array<string | null | undefined> = [
    tag?.id,
    tag?.identifier,
    tag?.serialNumber,
    decodeNdefPayload(tag?.ndefMessage),
  ];

  for (const candidate of candidates) {
    const normalized = normalizeEpc(candidate);
    if (normalized) return normalized;
  }

  return "";
}

export class PhoneNfcAdapter implements RfidReaderAdapter {
  readonly info: ReaderInfo = {
    id: "phone-nfc",
    name: "Phone NFC",
    manufacturer: "Generic",
    transport: "integrated",
    capabilities: { continuousScan: false },
  };

  private connected = false;
  private scanning = false;

  async isSupported(): Promise<boolean> {
    if (Platform.OS === "web") return false;
    return NfcManager.isSupported().catch(() => false);
  }

  async connect(): Promise<void> {
    const supported = await this.isSupported();
    if (!supported) {
      throw new Error("Phone NFC is not supported on this device.");
    }
    await NfcManager.start();
    this.connected = true;
  }

  async disconnect(): Promise<void> {
    this.connected = false;
    await this.stopScan();
  }

  async startScan(onRead: RfidReadListener): Promise<void> {
    if (!this.connected) {
      throw new Error("Phone NFC adapter is not connected.");
    }
    if (this.scanning) return;

    this.scanning = true;

    try {
      const enabled = await NfcManager.isEnabled().catch(() => true);
      if (!enabled) {
        throw new Error("NFC is disabled. Turn on NFC in system settings.");
      }

      const requestedTechs =
        Platform.OS === "ios"
          ? [NfcTech.Ndef, NfcTech.IsoDep, NfcTech.Iso15693IOS]
          : [
              NfcTech.Ndef,
              NfcTech.NfcA,
              NfcTech.NfcV,
              NfcTech.IsoDep,
              NfcTech.MifareClassic,
              NfcTech.MifareUltralight,
            ];

      await NfcManager.requestTechnology(requestedTechs, {
        alertMessage: "Hold your phone near the RFID tag.",
      });
      const tag = await NfcManager.getTag();
      const epc = extractEpcFromTag(tag as any);
      if (!epc) {
        throw new Error("No EPC/identifier was found on this tag.");
      }

      onRead({
        epc,
        readerId: this.info.id,
        manufacturer: this.info.manufacturer,
        timestamp: Date.now(),
        raw: tag,
      });
    } finally {
      this.scanning = false;
      NfcManager.cancelTechnologyRequest().catch(() => undefined);
    }
  }

  async stopScan(): Promise<void> {
    this.scanning = false;
    await NfcManager.cancelTechnologyRequest().catch(() => undefined);
  }
}

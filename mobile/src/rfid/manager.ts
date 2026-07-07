import { buildRfidAdapterRegistry } from "./registry";
import type { ReaderInfo, RfidReadListener, RfidReaderAdapter, StandardRfidRead } from "./types";

export class RfidManager {
  private readonly adapters = new Map<string, RfidReaderAdapter>();
  private activeAdapterId: string | null = null;
  private readonly listeners = new Set<RfidReadListener>();

  constructor() {
    for (const adapter of buildRfidAdapterRegistry()) {
      this.adapters.set(adapter.info.id, adapter);
    }

    this.activeAdapterId = process.env.EXPO_PUBLIC_RFID_ADAPTER ?? "phone-nfc";
    if (!this.activeAdapterId || !this.adapters.has(this.activeAdapterId)) {
      this.activeAdapterId = this.adapters.keys().next().value ?? null;
    }
  }

  getAvailableReaders(): ReaderInfo[] {
    return [...this.adapters.values()].map((adapter) => adapter.info);
  }

  getSelectedReader(): ReaderInfo | null {
    if (!this.activeAdapterId) return null;
    return this.adapters.get(this.activeAdapterId)?.info ?? null;
  }

  selectReader(readerId: string): void {
    if (!this.adapters.has(readerId)) {
      throw new Error(`RFID reader adapter not found: ${readerId}`);
    }
    this.activeAdapterId = readerId;
  }

  async isSelectedReaderSupported(): Promise<boolean> {
    const adapter = this.requireActiveAdapter();
    return adapter.isSupported();
  }

  async connect(): Promise<void> {
    const adapter = this.requireActiveAdapter();
    await adapter.connect();
  }

  async disconnect(): Promise<void> {
    const adapter = this.requireActiveAdapter();
    await adapter.disconnect();
  }

  async startScan(): Promise<void> {
    const adapter = this.requireActiveAdapter();
    await adapter.startScan((read) => {
      const normalized: StandardRfidRead = {
        ...read,
        epc: (read.epc || "").trim().toUpperCase(),
        timestamp: read.timestamp || Date.now(),
      };
      for (const listener of this.listeners) {
        listener(normalized);
      }
    });
  }

  async stopScan(): Promise<void> {
    const adapter = this.requireActiveAdapter();
    await adapter.stopScan();
  }

  onRead(listener: RfidReadListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private requireActiveAdapter(): RfidReaderAdapter {
    if (!this.activeAdapterId) {
      throw new Error("No RFID adapter is configured.");
    }
    const adapter = this.adapters.get(this.activeAdapterId);
    if (!adapter) {
      throw new Error(`RFID adapter '${this.activeAdapterId}' is not registered.`);
    }
    return adapter;
  }
}

export const rfidManager = new RfidManager();

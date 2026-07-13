import { buildRfidAdapterRegistry } from "./registry";
import type { ReaderInfo, RfidReadListener, RfidReaderAdapter, StandardRfidRead } from "./types";

export class RfidManager {
  private readonly adapters = new Map<string, RfidReaderAdapter>();
  private activeAdapterId: string | null = null;
  private readonly listeners = new Set<RfidReadListener>();
  private connected = false;
  private scanning = false;
  private scanSession = 0;

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
    if (this.connected) return;
    const adapter = this.requireActiveAdapter();
    await adapter.connect();
    this.connected = true;
  }

  async disconnect(): Promise<void> {
    if (this.scanning) {
      await this.stopScan();
    }
    if (!this.connected) return;
    const adapter = this.requireActiveAdapter();
    await adapter.disconnect();
    this.connected = false;
  }

  async startScan(): Promise<void> {
    if (this.scanning) return;
    const adapter = this.requireActiveAdapter();

    const session = ++this.scanSession;
    this.scanning = true;

    try {
      await adapter.startScan((read) => {
        if (!this.scanning || session !== this.scanSession) return;

        const normalized: StandardRfidRead = {
          ...read,
          epc: (read.epc || "").trim().toUpperCase(),
          timestamp: read.timestamp || Date.now(),
        };

        for (const listener of this.listeners) {
          try {
            listener(normalized);
          } catch {
            // Keep dispatching reads even if one listener throws.
          }
        }
      });
    } catch (error) {
      this.scanning = false;
      throw error;
    }
  }

  async stopScan(): Promise<void> {
    if (!this.scanning) {
      return;
    }

    this.scanSession++;
    this.scanning = false;

    const adapter = this.requireActiveAdapter();
    await adapter.stopScan();
  }

  isConnected(): boolean {
    return this.connected;
  }

  isScanning(): boolean {
    return this.scanning;
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

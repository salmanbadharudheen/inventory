import type { ReaderInfo, RfidReadListener, RfidReaderAdapter } from "../types";
import {
  freeDeviceApiReader,
  initializeDeviceApiReader,
  isDeviceApiBridgeAvailable,
  startDeviceApiInventory,
  stopDeviceApiInventory,
} from "../native/deviceapi-bridge";

export class RscjaCompatibleUhfAdapter implements RfidReaderAdapter {
  readonly info: ReaderInfo;

  private connected = false;
  private unsubscribe: (() => void) | null = null;

  constructor(info: ReaderInfo) {
    this.info = info;
  }

  async isSupported(): Promise<boolean> {
    return isDeviceApiBridgeAvailable();
  }

  async connect(): Promise<void> {
    if (this.connected) return;
    await initializeDeviceApiReader();
    this.connected = true;
  }

  async disconnect(): Promise<void> {
    await this.stopScan();
    await freeDeviceApiReader();
    this.connected = false;
  }

  async startScan(onRead: RfidReadListener): Promise<void> {
    if (!this.connected) {
      throw new Error(`${this.info.name} adapter is not connected.`);
    }

    if (this.unsubscribe) return;

    this.unsubscribe = await startDeviceApiInventory((read) => {
      onRead({
        epc: read.epc,
        rssi: read.rssi,
        readerId: this.info.id,
        manufacturer: this.info.manufacturer,
        timestamp: Date.now(),
        raw: read.raw,
      });
    });
  }

  async stopScan(): Promise<void> {
    this.unsubscribe?.();
    this.unsubscribe = null;
    await stopDeviceApiInventory();
  }
}
import type { ReaderInfo, RfidReadListener, RfidReaderAdapter } from "../types";
import {
  freeDeviceApiReader,
  initializeDeviceApiReader,
  isDeviceApiBridgeAvailable,
  startDeviceApiInventory,
  stopDeviceApiInventory,
} from "../native/deviceapi-bridge";

export class RscjaDeviceApiUhfAdapter implements RfidReaderAdapter {
  readonly info: ReaderInfo = {
    id: "rscja-deviceapi-uhf",
    name: "RSCJA DeviceAPI UHF",
    manufacturer: "RSCJA",
    transport: "integrated",
    capabilities: { continuousScan: true, supportsRssi: true },
  };

  private connected = false;
  private unsubscribe: (() => void) | null = null;

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
      throw new Error("RSCJA DeviceAPI adapter is not connected.");
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

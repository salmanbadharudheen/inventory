import type { ReaderInfo, RfidReadListener, RfidReaderAdapter } from "../types";
import { normalizeEpc } from "../utils/normalize";

const MOCK_EPCS = [
  "E20034120123456789ABCDEF",
  "E20034120123456789ABCDE0",
  "E20034120123456789ABCDE1",
  "E20034120123456789ABCDE2",
  "E20034120123456789ABCDE3",
];

export class MockUhfAdapter implements RfidReaderAdapter {
  readonly info: ReaderInfo = {
    id: "mock-uhf",
    name: "Mock UHF Reader",
    manufacturer: "Test",
    transport: "integrated",
    capabilities: { continuousScan: true, supportsRssi: true },
  };

  private connected = false;
  private timer: ReturnType<typeof setInterval> | null = null;

  async isSupported(): Promise<boolean> {
    return true;
  }

  async connect(): Promise<void> {
    this.connected = true;
  }

  async disconnect(): Promise<void> {
    this.connected = false;
    await this.stopScan();
  }

  async startScan(onRead: RfidReadListener): Promise<void> {
    if (!this.connected) {
      throw new Error("Mock UHF reader is not connected.");
    }
    if (this.timer) return;

    this.timer = setInterval(() => {
      const epc = MOCK_EPCS[Math.floor(Math.random() * MOCK_EPCS.length)];
      onRead({
        epc: normalizeEpc(epc),
        readerId: this.info.id,
        manufacturer: this.info.manufacturer,
        timestamp: Date.now(),
        rssi: -45 - Math.floor(Math.random() * 20),
        raw: { source: "mock" },
      });
    }, 1200);
  }

  async stopScan(): Promise<void> {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
  }
}

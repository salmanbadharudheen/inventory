import type { ReaderInfo, RfidReadListener, RfidReaderAdapter } from "../types";

export class UnsupportedUhfAdapter implements RfidReaderAdapter {
  readonly info: ReaderInfo;

  constructor(info: ReaderInfo) {
    this.info = info;
  }

  async isSupported(): Promise<boolean> {
    return false;
  }

  async connect(): Promise<void> {
    throw new Error(`${this.info.name} adapter is not wired yet. Add the vendor Android SDK bridge module.`);
  }

  async disconnect(): Promise<void> {
    return;
  }

  async startScan(_onRead: RfidReadListener): Promise<void> {
    throw new Error(`${this.info.name} adapter is not wired yet. Add the vendor Android SDK bridge module.`);
  }

  async stopScan(): Promise<void> {
    return;
  }
}

export type ReaderTransport = "integrated" | "bluetooth" | "sled" | "usb";

export interface ReaderCapabilities {
  continuousScan: boolean;
  supportsRssi?: boolean;
}

export interface ReaderInfo {
  id: string;
  name: string;
  manufacturer: string;
  transport: ReaderTransport;
  capabilities: ReaderCapabilities;
}

export interface StandardRfidRead {
  epc: string;
  readerId: string;
  manufacturer: string;
  timestamp: number;
  rssi?: number;
  raw?: unknown;
}

export type RfidReadListener = (read: StandardRfidRead) => void;

export interface RfidReaderAdapter {
  readonly info: ReaderInfo;
  isSupported(): Promise<boolean>;
  connect(): Promise<void>;
  disconnect(): Promise<void>;
  startScan(onRead: RfidReadListener): Promise<void>;
  stopScan(): Promise<void>;
}

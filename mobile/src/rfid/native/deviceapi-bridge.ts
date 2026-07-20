import { NativeEventEmitter, NativeModules, Platform } from "react-native";
import { normalizeEpc } from "../utils/normalize";

const MODULE_NAME = "RscjaDeviceApiModule";
const TAG_EVENT_NAME = "onRfidTag";

type NativeTagPayload = {
  epc?: string;
  rssi?: number;
  tid?: string;
  pc?: string;
  [key: string]: unknown;
};

type RscjaDeviceApiNativeModule = {
  initialize: () => Promise<boolean>;
  startInventory: () => Promise<boolean>;
  stopInventory: () => Promise<boolean>;
  free: () => Promise<boolean>;
  setReaderPower: (power: number) => Promise<DeviceApiPowerSetResult>;
  getReaderPower: () => Promise<DeviceApiPowerGetResult>;
  isSdkAvailable: () => Promise<boolean>;
  getDebugStatus: () => Promise<DeviceApiDebugStatus>;
  testSdkBinding: () => Promise<DeviceApiBindingTestResult>;
};

const nativeModule =
  (NativeModules[MODULE_NAME] as RscjaDeviceApiNativeModule | undefined) ??
  undefined;

const eventEmitter = nativeModule
  ? new NativeEventEmitter(nativeModule as never)
  : null;

export type DeviceApiTagRead = {
  epc: string;
  rssi?: number;
  raw?: NativeTagPayload;
};

export type DeviceApiDebugStatus = {
  initialized: boolean;
  hasReaderInstance: boolean;
  hasInventoryCallback: boolean;
  readerClassAvailable: boolean;
  callbackClassAvailable: boolean;
  readerInstanceClass?: string;
};

export type DeviceApiBindingTestResult = {
  ok: boolean;
  readerClass?: string;
  callbackClass?: string;
  error?: string;
};

export type DeviceApiPowerSetResult = {
  ok: boolean;
  power?: number;
  methodUsed?: string;
  error?: string;
};

export type DeviceApiPowerGetResult = {
  ok: boolean;
  power?: number;
  methodUsed?: string;
  error?: string;
};

export function isDeviceApiBridgeAvailable(): boolean {
  return Platform.OS === "android" && !!nativeModule;
}

export async function initializeDeviceApiReader(): Promise<void> {
  if (!isDeviceApiBridgeAvailable() || !nativeModule) {
    throw new Error(
      "RscjaDeviceApiModule is unavailable. Build an Android dev/production app with the native module linked."
    );
  }

  const ok = await nativeModule.initialize();
  if (!ok) {
    throw new Error("Failed to initialize RSCJA DeviceAPI reader.");
  }
}

export async function startDeviceApiInventory(
  onRead: (read: DeviceApiTagRead) => void
): Promise<() => void> {
  if (!isDeviceApiBridgeAvailable() || !nativeModule || !eventEmitter) {
    throw new Error(
      "RscjaDeviceApiModule is unavailable. Build an Android dev/production app with the native module linked."
    );
  }

  const subscription = eventEmitter.addListener(
    TAG_EVENT_NAME,
    (payload: NativeTagPayload) => {
      const epc = normalizeEpc(String(payload?.epc ?? ""));
      if (!epc) return;

      const rssiValue = payload?.rssi;
      onRead({
        epc,
        rssi:
          typeof rssiValue === "number"
            ? rssiValue
            : typeof rssiValue === "string"
              ? Number(rssiValue)
              : undefined,
        raw: payload,
      });
    }
  );

  try {
    const ok = await nativeModule.startInventory();
    if (!ok) {
      subscription.remove();
      throw new Error("Failed to start inventory scan using DeviceAPI.");
    }
  } catch (error) {
    subscription.remove();
    throw error;
  }

  return () => {
    subscription.remove();
  };
}

export async function stopDeviceApiInventory(): Promise<void> {
  if (!isDeviceApiBridgeAvailable() || !nativeModule) return;
  await nativeModule.stopInventory().catch(() => false);
}

export async function freeDeviceApiReader(): Promise<void> {
  if (!isDeviceApiBridgeAvailable() || !nativeModule) return;
  await nativeModule.free().catch(() => false);
}

export async function setDeviceApiReaderPower(power: number): Promise<DeviceApiPowerSetResult | null> {
  if (!isDeviceApiBridgeAvailable() || !nativeModule) return null;
  return nativeModule.setReaderPower(power).catch(() => null);
}

export async function getDeviceApiReaderPower(): Promise<DeviceApiPowerGetResult | null> {
  if (!isDeviceApiBridgeAvailable() || !nativeModule) return null;
  return nativeModule.getReaderPower().catch(() => null);
}

export async function isDeviceApiSdkAvailable(): Promise<boolean> {
  if (!isDeviceApiBridgeAvailable() || !nativeModule) return false;
  return nativeModule.isSdkAvailable().catch(() => false);
}

export async function getDeviceApiDebugStatus(): Promise<DeviceApiDebugStatus | null> {
  if (!isDeviceApiBridgeAvailable() || !nativeModule) return null;
  return nativeModule.getDebugStatus().catch(() => null);
}

export async function testDeviceApiSdkBinding(): Promise<DeviceApiBindingTestResult | null> {
  if (!isDeviceApiBridgeAvailable() || !nativeModule) return null;
  return nativeModule.testSdkBinding().catch(() => null);
}

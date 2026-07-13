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

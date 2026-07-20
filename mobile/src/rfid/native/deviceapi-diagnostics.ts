import {
  getDeviceApiDebugStatus,
  isDeviceApiBridgeAvailable,
  isDeviceApiSdkAvailable,
  testDeviceApiSdkBinding,
} from "./deviceapi-bridge";

export type DeviceApiDiagnostics = {
  bridgeAvailable: boolean;
  sdkAvailable: boolean;
  debugStatus: Awaited<ReturnType<typeof getDeviceApiDebugStatus>>;
  bindingTest: Awaited<ReturnType<typeof testDeviceApiSdkBinding>>;
};

export async function runDeviceApiDiagnostics(): Promise<DeviceApiDiagnostics> {
  const bridgeAvailable = isDeviceApiBridgeAvailable();

  if (!bridgeAvailable) {
    return {
      bridgeAvailable,
      sdkAvailable: false,
      debugStatus: null,
      bindingTest: null,
    };
  }

  const sdkAvailable = await isDeviceApiSdkAvailable();
  const [debugStatus, bindingTest] = await Promise.all([
    getDeviceApiDebugStatus(),
    testDeviceApiSdkBinding(),
  ]);

  return {
    bridgeAvailable,
    sdkAvailable,
    debugStatus,
    bindingTest,
  };
}
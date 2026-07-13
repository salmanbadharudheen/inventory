# RSCJA DeviceAPI Native Bridge Contract

This app expects an Android native module named `RscjaDeviceApiModule`.

## Required methods

The module must expose these async methods to JavaScript:

- `initialize(): Promise<boolean>`
- `startInventory(): Promise<boolean>`
- `stopInventory(): Promise<boolean>`
- `free(): Promise<boolean>`

## Required event

Emit RFID reads through event name:

- `onRfidTag`

Event payload shape expected by JS:

- `epc: string` (required)
- `rssi?: number`
- Any extra native fields are passed through as `raw`.

## JS integration points

- Bridge: `src/rfid/native/deviceapi-bridge.ts`
- Adapter: `src/rfid/adapters/rscja-deviceapi-uhf.ts`
- Registry: `src/rfid/registry.ts`

## Expo native scaffold

The Expo config plugin `plugins/with-rscja-deviceapi-sdk.js` copies:

- `vendor-sdk/API_Ver20251103/DeviceAPI_ver20251103_release.aar`

into:

- `android/app/libs/`

and adds this dependency in `android/app/build.gradle`:

- `implementation files('libs/DeviceAPI_ver20251103_release.aar')`

Run these commands after changes:

1. `npx expo prebuild --clean`
2. `npx expo run:android`

Use a physical Android device for testing UHF scanning.

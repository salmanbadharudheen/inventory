# RFID Integration Architecture (Multi-Vendor)

This module provides a hardware-independent RFID integration layer for the mobile app.

## Core design

- `RfidReaderAdapter` interface in `types.ts` defines a standard contract:
  - `connect()`
  - `disconnect()`
  - `startScan(onRead)`
  - `stopScan()`
- `RfidManager` in `manager.ts` owns adapter selection, lifecycle, and standardized read events.
- `StandardRfidRead` is the common payload used by UI/business logic.
- `scan-asset.tsx` depends only on `rfidManager`, not vendor SDKs.

## Current adapters

- `PhoneNfcAdapter` (`adapters/phone-nfc.ts`): generic phone NFC reader path.
- `MockUhfAdapter` (`adapters/mock-uhf.ts`): local testing/demo adapter.
- Vendor placeholders (`adapters/vendor-placeholders.ts`):
  - EXARK
  - Zebra
  - Chainway
  - Honeywell

These placeholders intentionally throw until native SDK bridges are implemented.

## Adding a real vendor adapter

1. Build a native Android bridge for the vendor SDK.
2. Implement `RfidReaderAdapter` in `src/rfid/adapters/<vendor>-uhf.ts`.
3. Normalize EPC with `normalizeEpc` from `utils/normalize.ts`.
4. Register adapter in `registry.ts`.

## Expo/React Native requirements

Production UHF integrations need native Android code and cannot rely on Expo Go.

Recommended setup:

- Use custom Expo development builds (or bare RN workflow).
- Add vendor SDK AAR/JAR dependencies in native Android project.
- Expose scan callbacks to JS via a native module.
- Keep UI and API lookup unchanged because they consume standardized `StandardRfidRead`.

## Runtime selection

- Default adapter is `phone-nfc`.
- Override with env var: `EXPO_PUBLIC_RFID_ADAPTER=<adapter-id>`.
- Reader can also be switched at runtime from the Scan Asset screen.

## Lookup behavior

Scan flow remains the same for every vendor:

1. Adapter emits standardized EPC value.
2. App calls `lookupAssetByRfidTag(epc)`.
3. Asset details shown when matched.
4. `Unknown RFID Tag / Asset Not Registered` shown when no match.

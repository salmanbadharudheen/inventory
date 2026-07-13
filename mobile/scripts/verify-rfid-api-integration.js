const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..");

function read(relPath) {
  return fs.readFileSync(path.join(root, relPath), "utf8");
}

function assertContains(relPath, expected) {
  const text = read(relPath);
  if (!text.includes(expected)) {
    throw new Error(`Expected '${expected}' in ${relPath}`);
  }
}

function run() {
  // Service-level API contract checks.
  assertContains("src/services/asset-api.ts", "export async function lookupAssetByRfidTag(");
  assertContains("src/services/asset-api.ts", "?rfid_tag=");
  assertContains("src/services/asset-api.ts", "export async function updateAssetRfidTag(");
  assertContains("src/services/asset-api.ts", "/rfid-tag/");

  // UI integration checks (existing flow should stay unchanged).
  assertContains("app/(app)/scan-asset.tsx", "lookupAssetByRfidTag");
  assertContains("app/(app)/scan-asset.tsx", "rfidManager.startScan");
  assertContains("app/(app)/scan-asset.tsx", "rfidManager.stopScan");

  assertContains("app/(app)/room-inventory.tsx", "lookupAssetByRfidTag");
  assertContains("app/(app)/room-inventory.tsx", "rfidManager.startScan");
  assertContains("app/(app)/room-inventory.tsx", "rfidManager.stopScan");

  // New adapter wiring checks.
  assertContains("src/rfid/registry.ts", "new RscjaDeviceApiUhfAdapter()");
  assertContains("src/rfid/adapters/rscja-deviceapi-uhf.ts", "startDeviceApiInventory");

  console.log("RFID API + integration verification passed.");
}

try {
  run();
  process.exit(0);
} catch (error) {
  console.error(String(error && error.message ? error.message : error));
  process.exit(1);
}

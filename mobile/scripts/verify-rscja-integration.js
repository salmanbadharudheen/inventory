const fs = require("fs");
const path = require("path");

const projectRoot = path.resolve(__dirname, "..");

function mustExist(relPath) {
  const full = path.join(projectRoot, relPath);
  if (!fs.existsSync(full)) {
    throw new Error(`Missing required file: ${relPath}`);
  }
}

function mustContain(relPath, snippet) {
  const full = path.join(projectRoot, relPath);
  const text = fs.readFileSync(full, "utf8");
  if (!text.includes(snippet)) {
    throw new Error(`Expected snippet not found in ${relPath}: ${snippet}`);
  }
}

function run() {
  mustExist("vendor-sdk/API_Ver20251103/DeviceAPI_ver20251103_release.aar");
  mustExist("android/app/libs/DeviceAPI_ver20251103_release.aar");
  mustExist("android/app/src/main/java/com/inventory/mobile/rfid/RscjaDeviceApiModule.kt");
  mustExist("android/app/src/main/java/com/inventory/mobile/rfid/RscjaDeviceApiPackage.kt");

  mustContain(
    "android/app/build.gradle",
    "implementation files('libs/DeviceAPI_ver20251103_release.aar')"
  );
  mustContain(
    "android/app/src/main/java/com/inventory/mobile/MainApplication.kt",
    "add(RscjaDeviceApiPackage())"
  );

  mustContain("src/rfid/native/deviceapi-bridge.ts", "RscjaDeviceApiModule");
  mustContain("src/rfid/adapters/rscja-deviceapi-uhf.ts", "startDeviceApiInventory");

  console.log("RSCJA integration scaffold verification passed.");
}

try {
  run();
  process.exit(0);
} catch (error) {
  console.error(String(error && error.message ? error.message : error));
  process.exit(1);
}

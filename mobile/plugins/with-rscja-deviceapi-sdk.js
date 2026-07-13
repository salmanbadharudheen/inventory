const fs = require("fs");
const path = require("path");
const {
  createRunOncePlugin,
  withAppBuildGradle,
  withDangerousMod,
} = require("@expo/config-plugins");

const PLUGIN_NAME = "with-rscja-deviceapi-sdk";
const PLUGIN_VERSION = "1.0.0";
const AAR_FILE_NAME = "DeviceAPI_ver20251103_release.aar";
const SOURCE_AAR_PATH = path.join(
  "vendor-sdk",
  "API_Ver20251103",
  AAR_FILE_NAME
);

function ensureAarCopied(projectRoot) {
  const sourcePath = path.join(projectRoot, SOURCE_AAR_PATH);
  const targetDir = path.join(projectRoot, "android", "app", "libs");
  const targetPath = path.join(targetDir, AAR_FILE_NAME);

  if (!fs.existsSync(sourcePath)) {
    throw new Error(
      `[${PLUGIN_NAME}] SDK AAR not found at ${sourcePath}. Place the vendor SDK file before running prebuild.`
    );
  }

  fs.mkdirSync(targetDir, { recursive: true });
  fs.copyFileSync(sourcePath, targetPath);
}

function ensureAarDependency(contents) {
  const dependencyLine = `    implementation files('libs/${AAR_FILE_NAME}')`;
  if (contents.includes(dependencyLine)) {
    return contents;
  }

  if (!contents.match(/dependencies\s*\{/)) {
    throw new Error(
      `[${PLUGIN_NAME}] Could not find dependencies block in android/app/build.gradle.`
    );
  }

  return contents.replace(
    /dependencies\s*\{/,
    `dependencies {\n${dependencyLine}`
  );
}

function withRscjaDeviceApiSdk(config) {
  config = withDangerousMod(config, ["android", async (modConfig) => {
    ensureAarCopied(modConfig.modRequest.projectRoot);
    return modConfig;
  }]);

  config = withAppBuildGradle(config, (modConfig) => {
    modConfig.modResults.contents = ensureAarDependency(
      modConfig.modResults.contents
    );
    return modConfig;
  });

  return config;
}

module.exports = createRunOncePlugin(
  withRscjaDeviceApiSdk,
  PLUGIN_NAME,
  PLUGIN_VERSION
);

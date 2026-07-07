import { UnsupportedUhfAdapter } from "./unsupported-uhf";

export const exarkAdapter = new UnsupportedUhfAdapter({
  id: "exark-uhf",
  name: "EXARK UHF Reader",
  manufacturer: "EXARK",
  transport: "bluetooth",
  capabilities: { continuousScan: true, supportsRssi: true },
});

export const zebraAdapter = new UnsupportedUhfAdapter({
  id: "zebra-uhf",
  name: "Zebra UHF Reader",
  manufacturer: "Zebra",
  transport: "bluetooth",
  capabilities: { continuousScan: true, supportsRssi: true },
});

export const chainwayAdapter = new UnsupportedUhfAdapter({
  id: "chainway-uhf",
  name: "Chainway UHF Reader",
  manufacturer: "Chainway",
  transport: "integrated",
  capabilities: { continuousScan: true, supportsRssi: true },
});

export const honeywellAdapter = new UnsupportedUhfAdapter({
  id: "honeywell-uhf",
  name: "Honeywell UHF Reader",
  manufacturer: "Honeywell",
  transport: "integrated",
  capabilities: { continuousScan: true, supportsRssi: true },
});

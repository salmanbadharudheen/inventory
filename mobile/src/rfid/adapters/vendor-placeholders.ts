import { RscjaCompatibleUhfAdapter } from "./rscja-compatible-uhf";

export const exarkAdapter = new RscjaCompatibleUhfAdapter({
  id: "exark-uhf",
  name: "EXARK UHF Reader",
  manufacturer: "EXARK",
  transport: "bluetooth",
  capabilities: { continuousScan: true, supportsRssi: true },
});

export const zebraAdapter = new RscjaCompatibleUhfAdapter({
  id: "zebra-uhf",
  name: "Zebra UHF Reader",
  manufacturer: "Zebra",
  transport: "bluetooth",
  capabilities: { continuousScan: true, supportsRssi: true },
});

export const chainwayAdapter = new RscjaCompatibleUhfAdapter({
  id: "chainway-uhf",
  name: "Chainway UHF Reader",
  manufacturer: "Chainway",
  transport: "integrated",
  capabilities: { continuousScan: true, supportsRssi: true },
});

export const honeywellAdapter = new RscjaCompatibleUhfAdapter({
  id: "honeywell-uhf",
  name: "Honeywell UHF Reader",
  manufacturer: "Honeywell",
  transport: "integrated",
  capabilities: { continuousScan: true, supportsRssi: true },
});

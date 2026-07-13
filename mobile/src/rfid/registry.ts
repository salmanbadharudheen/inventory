import { MockUhfAdapter } from "./adapters/mock-uhf";
import { PhoneNfcAdapter } from "./adapters/phone-nfc";
import { RscjaDeviceApiUhfAdapter } from "./adapters/rscja-deviceapi-uhf";
import {
  chainwayAdapter,
  exarkAdapter,
  honeywellAdapter,
  zebraAdapter,
} from "./adapters/vendor-placeholders";
import type { RfidReaderAdapter } from "./types";

export function buildRfidAdapterRegistry(): RfidReaderAdapter[] {
  return [
    new PhoneNfcAdapter(),
    new RscjaDeviceApiUhfAdapter(),
    new MockUhfAdapter(),
    exarkAdapter,
    zebraAdapter,
    chainwayAdapter,
    honeywellAdapter,
  ];
}

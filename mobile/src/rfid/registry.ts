import { MockUhfAdapter } from "./adapters/mock-uhf";
import { PhoneNfcAdapter } from "./adapters/phone-nfc";
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
    new MockUhfAdapter(),
    exarkAdapter,
    zebraAdapter,
    chainwayAdapter,
    honeywellAdapter,
  ];
}

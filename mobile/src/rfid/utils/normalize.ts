export function normalizeEpc(value: string | null | undefined): string {
  if (!value) return "";
  return value
    .trim()
    .replace(/[\s.,;:!"'`]+$/g, "")
    .replace(/[\s:-]+/g, "")
    .toUpperCase();
}

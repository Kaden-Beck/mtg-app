/**
 * Parses raw OCR text from the collector-number corner into a
 * { setCode, collectorNumber } pair suitable for an exact Scryfall lookup.
 *
 * Deliberately dumb by design (per the reuse brief): no fuzzy matching, no
 * dictionary of set names. The corner print is small and near-fixed-format,
 * so a couple of regexes covering the orderings OCR tends to produce is
 * enough - if nothing matches, the scan is rejected and the user re-aligns.
 */

export interface ParsedCollectorNumber {
  setCode: string
  collectorNumber: string
}

// "FDN U 0125" / "FDN • U • 0125" - set, rarity, number
const SET_RARITY_NUMBER =
  /\b([A-Z0-9]{2,5})\D{1,3}([A-CMRSTU])\D{1,3}(\d{1,4}[A-Za-z★]?)\b/

// "0125/281 U FDN" - number[/total], rarity, set
const NUMBER_RARITY_SET =
  /\b(\d{1,4}[A-Za-z★]?)\s*\/?\s*\d{0,4}\D{1,3}([A-CMRSTU])\D{1,3}([A-Z0-9]{2,5})\b/

function clean(raw: string): string {
  return raw
    .toUpperCase()
    .replace(/[^A-Z0-9/\s]/g, " ")
    .replace(/\s+/g, " ")
    .trim()
}

export function parseCollectorNumberText(raw: string): ParsedCollectorNumber | null {
  const text = clean(raw)
  if (text.length < 4 || text.length > 30) return null

  const setRarityNumber = text.match(SET_RARITY_NUMBER)
  if (setRarityNumber) {
    return { setCode: setRarityNumber[1], collectorNumber: setRarityNumber[3] }
  }

  const numberRaritySet = text.match(NUMBER_RARITY_SET)
  if (numberRaritySet) {
    return { setCode: numberRaritySet[3], collectorNumber: numberRaritySet[1] }
  }

  // Loose fallback: any bare set-code-shaped token plus any bare number
  // token, regardless of order or separators.
  const setToken = text.match(/\b[A-Z0-9]{3,5}\b/)
  const numberToken = text.match(/\b\d{1,4}[A-Za-z★]?\b/)
  if (setToken && numberToken) {
    return { setCode: setToken[0], collectorNumber: numberToken[0] }
  }

  return null
}

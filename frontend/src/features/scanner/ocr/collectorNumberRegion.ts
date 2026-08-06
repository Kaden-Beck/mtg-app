/**
 * Collector-number crop regions. Independent implementation; the approach
 * (crop a few fixed guesses at the bottom-left corner instead of segmenting
 * the whole card) was informed by GrimbiXcode/mtgscan
 * (https://github.com/GrimbiXcode/mtgscan, GPL-3.0 per its LICENSE.md - its
 * README's "MIT" claim does not match). No code from that repo was copied
 * - see /NOTICE for the full attribution and license note.
 *
 * The lesson that repo landed on after iterating past full-frame card
 * detection: don't segment the card, just crop a few fixed guesses at the
 * bottom-left corner (where the collector number lives) against a frame the
 * user has already aligned to an on-screen guide, and let OCR fallback
 * scoring pick the best one.
 */

export interface CropRegion {
  name: "optimal" | "wider" | "offset"
  /** Fractional rect (0-1) relative to the aligned card image. */
  x: number
  y: number
  width: number
  height: number
}

export const COLLECTOR_NUMBER_REGIONS: CropRegion[] = [
  { name: "optimal", x: 0.02, y: 0.92, width: 0.3, height: 0.065 },
  { name: "wider", x: 0.0, y: 0.895, width: 0.42, height: 0.09 },
  { name: "offset", x: 0.02, y: 0.885, width: 0.3, height: 0.065 },
]

/**
 * Crops one region out of a captured card image and upscales it, since
 * collector-number text is only a few pixels tall at typical capture
 * resolution and Tesseract does much better on larger glyphs.
 */
export function cropRegion(
  source: CanvasImageSource,
  sourceWidth: number,
  sourceHeight: number,
  region: CropRegion,
  scale = 3
): HTMLCanvasElement {
  const sx = region.x * sourceWidth
  const sy = region.y * sourceHeight
  const sw = region.width * sourceWidth
  const sh = region.height * sourceHeight

  const canvas = document.createElement("canvas")
  canvas.width = Math.round(sw * scale)
  canvas.height = Math.round(sh * scale)

  const ctx = canvas.getContext("2d")
  if (!ctx) throw new Error("2D canvas context unavailable")

  ctx.imageSmoothingEnabled = true
  ctx.imageSmoothingQuality = "high"
  ctx.drawImage(source, sx, sy, sw, sh, 0, 0, canvas.width, canvas.height)

  return canvas
}

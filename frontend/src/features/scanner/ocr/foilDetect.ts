/**
 * Foil-detection heuristic, ported from GrimbiXcode/mtgscan's
 * `detectFoilCard` (https://github.com/GrimbiXcode/mtgscan, MIT) - see
 * /NOTICE. Brightness/hue-variance based, no ML model involved: foil
 * treatments scatter light unevenly across the card face, so a foil capture
 * shows much higher local brightness and hue variance under normal room
 * lighting than a matte non-foil capture does.
 */

export interface FoilDetectionResult {
  isFoil: boolean
  confidence: number
}

// Sample the card face, away from the fixed-position text/border regions
// that would skew brightness stats regardless of foil treatment.
const SAMPLE_REGION = { x: 0.15, y: 0.15, width: 0.7, height: 0.55 }

const GRID_SIZE = 8
const BRIGHTNESS_STDDEV_THRESHOLD = 45
const HUE_VARIANCE_THRESHOLD = 0.08

function rgbToHue(r: number, g: number, b: number): number {
  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  const delta = max - min
  if (delta === 0) return 0

  let hue: number
  if (max === r) hue = ((g - b) / delta) % 6
  else if (max === g) hue = (b - r) / delta + 2
  else hue = (r - g) / delta + 4

  hue *= 60
  return hue < 0 ? hue + 360 : hue
}

export function detectFoilCard(
  source: CanvasImageSource,
  sourceWidth: number,
  sourceHeight: number
): FoilDetectionResult {
  const sx = SAMPLE_REGION.x * sourceWidth
  const sy = SAMPLE_REGION.y * sourceHeight
  const sw = SAMPLE_REGION.width * sourceWidth
  const sh = SAMPLE_REGION.height * sourceHeight

  const canvas = document.createElement("canvas")
  canvas.width = GRID_SIZE
  canvas.height = GRID_SIZE
  const ctx = canvas.getContext("2d")
  if (!ctx) throw new Error("2D canvas context unavailable")

  // Downscaling onto a small grid via drawImage does the block-averaging
  // for us - each output pixel represents one sample cell.
  ctx.drawImage(source, sx, sy, sw, sh, 0, 0, GRID_SIZE, GRID_SIZE)
  const { data } = ctx.getImageData(0, 0, GRID_SIZE, GRID_SIZE)

  const brightnesses: number[] = []
  const hues: number[] = []
  for (let i = 0; i < data.length; i += 4) {
    const r = data[i]
    const g = data[i + 1]
    const b = data[i + 2]
    brightnesses.push(0.299 * r + 0.587 * g + 0.114 * b)
    hues.push(rgbToHue(r, g, b) / 360)
  }

  const brightnessMean = brightnesses.reduce((a, b) => a + b, 0) / brightnesses.length
  const brightnessStdDev = Math.sqrt(
    brightnesses.reduce((sum, v) => sum + (v - brightnessMean) ** 2, 0) / brightnesses.length
  )

  const hueMean = hues.reduce((a, b) => a + b, 0) / hues.length
  const hueVariance = hues.reduce((sum, v) => sum + (v - hueMean) ** 2, 0) / hues.length

  const brightnessScore = Math.min(brightnessStdDev / BRIGHTNESS_STDDEV_THRESHOLD, 1.5)
  const hueScore = Math.min(hueVariance / HUE_VARIANCE_THRESHOLD, 1.5)
  const confidence = Math.min((brightnessScore + hueScore) / 2, 1)

  return {
    isFoil: brightnessStdDev > BRIGHTNESS_STDDEV_THRESHOLD || hueVariance > HUE_VARIANCE_THRESHOLD,
    confidence,
  }
}

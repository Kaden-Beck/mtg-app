/**
 * Multi-strategy OCR fallback + scoring. Independent implementation; the
 * approach (try each crop region in turn, score what comes back, stop as
 * soon as a result is good enough) was informed by GrimbiXcode/mtgscan's
 * `performCollectorNumberOCRWithFallback` (https://github.com/GrimbiXcode/mtgscan,
 * GPL-3.0 per its LICENSE.md - its README's "MIT" claim does not match). No
 * code from that repo was copied - see /NOTICE for the full attribution
 * and license note.
 */
import Tesseract from "tesseract.js"
import { COLLECTOR_NUMBER_REGIONS, cropRegion } from "./collectorNumberRegion"
import { parseCollectorNumberText, type ParsedCollectorNumber } from "./parseCollectorNumber"

export interface OcrAttempt {
  region: string
  text: string
  confidence: number
  parsed: ParsedCollectorNumber | null
  score: number
}

export interface OcrFallbackResult {
  best: OcrAttempt | null
  attempts: OcrAttempt[]
}

const EARLY_STOP_SCORE = 0.85

function scoreAttempt(confidence: number, parsed: ParsedCollectorNumber | null): number {
  if (!parsed) return 0
  // A confident parse is worth more than raw OCR confidence alone - a
  // low-confidence recognition that still cleanly matches the expected
  // "set + number" shape is a better signal than high confidence on
  // garbage that fails to parse.
  const parseScore = 0.6
  const confidenceScore = 0.4 * (confidence / 100)
  return parseScore + confidenceScore
}

export async function recognizeCollectorNumberWithFallback(
  source: CanvasImageSource,
  sourceWidth: number,
  sourceHeight: number,
  options: { earlyStopScore?: number } = {}
): Promise<OcrFallbackResult> {
  const earlyStopScore = options.earlyStopScore ?? EARLY_STOP_SCORE
  const attempts: OcrAttempt[] = []

  let worker: Tesseract.Worker | null = null
  try {
    worker = await Tesseract.createWorker("eng")
    await worker.setParameters({
      tessedit_char_whitelist: "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789/★• ",
    })

    for (const region of COLLECTOR_NUMBER_REGIONS) {
      const cropped = cropRegion(source, sourceWidth, sourceHeight, region)
      const { data } = await worker.recognize(cropped)
      const parsed = parseCollectorNumberText(data.text)
      const attempt: OcrAttempt = {
        region: region.name,
        text: data.text.trim(),
        confidence: data.confidence,
        parsed,
        score: scoreAttempt(data.confidence, parsed),
      }
      attempts.push(attempt)

      if (attempt.score >= earlyStopScore) break
    }
  } finally {
    await worker?.terminate()
  }

  const best = attempts.reduce<OcrAttempt | null>(
    (best, attempt) => (!best || attempt.score > best.score ? attempt : best),
    null
  )

  return { best, attempts }
}

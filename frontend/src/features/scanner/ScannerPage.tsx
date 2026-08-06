import { useCallback, useEffect, useRef, useState } from "react"
import { useLazyQuery, useMutation } from "@apollo/client/react"
import {
  AddToCollectionDocument,
  CardByCollectorNumberDocument,
} from "@/lib/gql/graphql"
import type {
  AddToCollectionMutation,
  AddToCollectionMutationVariables,
  CardByCollectorNumberQuery,
  CardByCollectorNumberQueryVariables,
} from "@/lib/gql/graphql"
import { Button } from "@/components/ui/button"
import { recognizeCollectorNumberWithFallback, type OcrAttempt } from "./ocr/ocrFallback"
import { detectFoilCard } from "./ocr/foilDetect"

type ScanStatus = "idle" | "scanning" | "looking-up" | "found" | "not-found" | "added"

// Physical MTG card size (63mm x 88mm) - used both for the on-screen guide
// frame and to crop the aligned card out of the video frame on capture.
const CARD_ASPECT_RATIO = 63 / 88

export function ScannerPage() {
  const videoRef = useRef<HTMLVideoElement>(null)
  const [status, setStatus] = useState<ScanStatus>("idle")
  const [cameraError, setCameraError] = useState<string | null>(null)
  const [attempts, setAttempts] = useState<OcrAttempt[]>([])
  const [isFoil, setIsFoil] = useState(false)

  const [lookupCard, { data: cardData }] = useLazyQuery<
    CardByCollectorNumberQuery,
    CardByCollectorNumberQueryVariables
  >(CardByCollectorNumberDocument)

  const [addToCollection, { loading: adding }] = useMutation<
    AddToCollectionMutation,
    AddToCollectionMutationVariables
  >(AddToCollectionDocument)

  useEffect(() => {
    let stream: MediaStream | null = null
    navigator.mediaDevices
      .getUserMedia({ video: { facingMode: "environment" } })
      .then((s) => {
        stream = s
        if (videoRef.current) videoRef.current.srcObject = s
      })
      .catch((err) => setCameraError(err instanceof Error ? err.message : "Camera unavailable"))

    return () => {
      stream?.getTracks().forEach((track) => track.stop())
    }
  }, [])

  const handleCapture = useCallback(async () => {
    const video = videoRef.current
    if (!video || video.videoWidth === 0) return

    setStatus("scanning")
    setAttempts([])

    // The user aligns the physical card to the guide frame overlay, so crop
    // to that rect (centered, card-aspect-ratio) rather than the full feed.
    const guideWidth = video.videoHeight * CARD_ASPECT_RATIO
    const sx = (video.videoWidth - guideWidth) / 2

    const canvas = document.createElement("canvas")
    canvas.width = guideWidth
    canvas.height = video.videoHeight
    const ctx = canvas.getContext("2d")
    if (!ctx) return
    ctx.drawImage(video, sx, 0, guideWidth, video.videoHeight, 0, 0, guideWidth, video.videoHeight)

    const { best, attempts: ocrAttempts } = await recognizeCollectorNumberWithFallback(
      canvas,
      canvas.width,
      canvas.height
    )
    setAttempts(ocrAttempts)

    if (!best?.parsed) {
      setStatus("not-found")
      return
    }

    setIsFoil(detectFoilCard(canvas, canvas.width, canvas.height).isFoil)

    setStatus("looking-up")
    const { data } = await lookupCard({
      variables: {
        setCode: best.parsed.setCode,
        collectorNumber: best.parsed.collectorNumber,
      },
    })

    setStatus(data?.cardByCollectorNumber ? "found" : "not-found")
  }, [lookupCard])

  const handleAdd = useCallback(async () => {
    const card = cardData?.cardByCollectorNumber
    if (!card) return
    await addToCollection({
      variables: { scryfallId: card.id, quantity: 1, foil: isFoil, condition: "NM" },
    })
    setStatus("added")
  }, [addToCollection, cardData, isFoil])

  const card = cardData?.cardByCollectorNumber
  const busy = status === "scanning" || status === "looking-up"

  return (
    <div className="flex flex-col items-center gap-4 p-4">
      <div className="relative w-full max-w-md overflow-hidden rounded-lg bg-black">
        <video ref={videoRef} autoPlay playsInline muted className="w-full" />
        <div
          className="pointer-events-none absolute inset-y-4 left-1/2 -translate-x-1/2 rounded-md border-2 border-white/80"
          style={{ aspectRatio: CARD_ASPECT_RATIO }}
        />
      </div>

      {cameraError && (
        <p role="alert" className="text-sm text-destructive">
          {cameraError}
        </p>
      )}

      <Button onClick={handleCapture} disabled={busy || !!cameraError}>
        {busy ? "Scanning..." : "Capture card"}
      </Button>

      {status === "not-found" && (
        <p className="text-sm text-muted-foreground">
          Couldn't read a collector number. Align the card to the guide frame and try again.
          {attempts.some((a) => a.text) && (
            <> (best guess: {attempts.map((a) => a.text || "-").join(" / ")})</>
          )}
        </p>
      )}

      {status === "found" && card && (
        <div className="flex flex-col items-center gap-2">
          <p>
            {card.name} — {card.setCode.toUpperCase()} #{card.collectorNumber}
            {isFoil && " (foil)"}
          </p>
          <Button onClick={handleAdd} disabled={adding}>
            {adding ? "Adding..." : "Add to collection"}
          </Button>
        </div>
      )}

      {status === "added" && <p className="text-sm">Added to collection.</p>}
    </div>
  )
}

import { useState, useEffect, useCallback } from 'react'

// Elapsed seconds since the first chat message (DESIGN.md §7). Call start()
// once; it's a no-op after the first call, matching "timer starts on first message".
// Accepts an initial start timestamp so a restored session keeps counting
// from when it actually started, not from the moment of the reload.
export function useElapsedTimer(initialStartedAt = null) {
  const [startedAt, setStartedAt] = useState(initialStartedAt)
  const [elapsedSeconds, setElapsedSeconds] = useState(
    initialStartedAt ? (Date.now() - initialStartedAt) / 1000 : 0,
  )

  useEffect(() => {
    const interval = setInterval(() => {
      setStartedAt((current) => {
        if (current) setElapsedSeconds((Date.now() - current) / 1000)
        return current
      })
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  const start = useCallback(() => {
    setStartedAt((current) => current ?? Date.now())
  }, [])

  const currentElapsedSeconds = useCallback(
    () => (startedAt ? (Date.now() - startedAt) / 1000 : 0),
    [startedAt],
  )

  const reset = useCallback(() => {
    setStartedAt(null)
    setElapsedSeconds(0)
  }, [])

  return { elapsedSeconds, start, currentElapsedSeconds, startedAt, reset }
}

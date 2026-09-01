import { useState, useEffect, useCallback } from 'react'

// Elapsed seconds since the first chat message (DESIGN.md §7). Call start()
// once; it's a no-op after the first call, matching "timer starts on first message".
// Accepts an initial start timestamp so a restored session keeps counting
// from when it actually started, not from the moment of the reload.
// If the session was already stopped (e.g. reloading a page after a passing
// submit), pass initialRunning=false and initialElapsedSeconds to restore the
// frozen value instead of resuming the count.
export function useElapsedTimer(initialStartedAt = null, initialRunning = true, initialElapsedSeconds = null) {
  const [startedAt, setStartedAt] = useState(initialStartedAt)
  const [elapsedSeconds, setElapsedSeconds] = useState(() => {
    if (initialElapsedSeconds != null) return initialElapsedSeconds
    return initialStartedAt ? (Date.now() - initialStartedAt) / 1000 : 0
  })

  const [running, setRunning] = useState(Boolean(initialStartedAt) && initialRunning)

  useEffect(() => {
    if (!running) return undefined
    const interval = setInterval(() => {
      setStartedAt((current) => {
        if (current) setElapsedSeconds((Date.now() - current) / 1000)
        return current
      })
    }, 1000)
    return () => clearInterval(interval)
  }, [running])

  const start = useCallback(() => {
    setStartedAt((current) => current ?? Date.now())
    setRunning(true)
  }, [])

  const currentElapsedSeconds = useCallback(
    () => (startedAt ? (Date.now() - startedAt) / 1000 : 0),
    [startedAt],
  )

  const stop = useCallback(() => {
    setElapsedSeconds((current) => {
      const start = startedAt
      return start ? (Date.now() - start) / 1000 : current
    })
    setRunning(false)
  }, [startedAt])

  const reset = useCallback(() => {
    setStartedAt(null)
    setElapsedSeconds(0)
    setRunning(false)
  }, [])

  return { elapsedSeconds, start, stop, currentElapsedSeconds, startedAt, reset }
}

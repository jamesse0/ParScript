import { useState, useEffect, useRef, useCallback } from 'react'

// Elapsed seconds since the first chat message (DESIGN.md §7). Call start()
// once; it's a no-op after the first call, matching "timer starts on first message".
export function useElapsedTimer() {
  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const startedAt = useRef(null)

  useEffect(() => {
    const interval = setInterval(() => {
      if (startedAt.current) {
        setElapsedSeconds((Date.now() - startedAt.current) / 1000)
      }
    }, 1000)
    return () => clearInterval(interval)
  }, [])

  const start = useCallback(() => {
    if (!startedAt.current) startedAt.current = Date.now()
  }, [])

  const currentElapsedSeconds = useCallback(
    () => (startedAt.current ? (Date.now() - startedAt.current) / 1000 : 0),
    [],
  )

  return { elapsedSeconds, start, currentElapsedSeconds }
}

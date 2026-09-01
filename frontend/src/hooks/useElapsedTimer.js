import { useState, useEffect, useRef, useCallback } from 'react'

// Accumulating stopwatch: it only advances while running, and start()/pause()
// bank time across many spans.
//
// - Prompt mode: the workspace resumes it for each LLM call and pauses it when
//   the response lands, so the displayed time is the total the user spent
//   waiting on the model across all back-and-forth turns.
// - Manual mode: resumed once when the page is ready and left running until the
//   solve passes.
//
// Takes the restored accumulated seconds so a reloaded session keeps its total;
// it always comes back paused and resumes on the next start().
export function useElapsedTimer(initialElapsedSeconds = 0) {
  const accumulatedRef = useRef(initialElapsedSeconds || 0)
  const runningSinceRef = useRef(null) // ms timestamp while running, null while paused
  const [elapsedSeconds, setElapsedSeconds] = useState(accumulatedRef.current)
  const [running, setRunning] = useState(false)

  const currentElapsedSeconds = useCallback(
    () =>
      accumulatedRef.current +
      (runningSinceRef.current != null ? (Date.now() - runningSinceRef.current) / 1000 : 0),
    [],
  )

  useEffect(() => {
    if (!running) return undefined
    const id = setInterval(() => setElapsedSeconds(currentElapsedSeconds()), 250)
    return () => clearInterval(id)
  }, [running, currentElapsedSeconds])

  const start = useCallback(() => {
    if (runningSinceRef.current != null) return // already running
    runningSinceRef.current = Date.now()
    setRunning(true)
  }, [])

  const pause = useCallback(() => {
    if (runningSinceRef.current == null) return // already paused
    accumulatedRef.current += (Date.now() - runningSinceRef.current) / 1000
    runningSinceRef.current = null
    setRunning(false)
    setElapsedSeconds(accumulatedRef.current)
  }, [])

  const reset = useCallback(() => {
    accumulatedRef.current = 0
    runningSinceRef.current = null
    setRunning(false)
    setElapsedSeconds(0)
  }, [])

  // Freezing on a passing submit is just a pause — nothing resumes it after.
  return { elapsedSeconds, running, start, pause, stop: pause, currentElapsedSeconds, reset }
}

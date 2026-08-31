import { useState, useCallback } from 'react'

// Accumulates input/output tokens across chat calls. Client-reported and
// trusted for tonight (DESIGN.md §9) — no server-side session ledger.
export function useTokenCounter() {
  const [inputTokens, setInputTokens] = useState(0)
  const [outputTokens, setOutputTokens] = useState(0)

  const addUsage = useCallback((input, output) => {
    setInputTokens((v) => v + input)
    setOutputTokens((v) => v + output)
  }, [])

  return { inputTokens, outputTokens, addUsage }
}

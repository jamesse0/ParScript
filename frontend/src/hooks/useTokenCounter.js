import { useState, useCallback } from 'react'

// Accumulates input/output tokens across chat calls. Client-reported and
// trusted for tonight (DESIGN.md §9) — no server-side session ledger.
// Accepts initial totals so a restored session keeps its running count.
export function useTokenCounter(initialInput = 0, initialOutput = 0) {
  const [inputTokens, setInputTokens] = useState(initialInput)
  const [outputTokens, setOutputTokens] = useState(initialOutput)

  const addUsage = useCallback((input, output) => {
    setInputTokens((v) => v + input)
    setOutputTokens((v) => v + output)
  }, [])

  return { inputTokens, outputTokens, addUsage }
}

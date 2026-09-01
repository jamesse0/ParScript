import { useState, useCallback } from 'react'

// Accumulates input/output/reasoning tokens across chat calls. Client-reported
// and trusted for tonight (DESIGN.md §9) — no server-side session ledger.
// Accepts initial totals so a restored session keeps its running count.
// Note: reasoning tokens are ALSO part of outputTokens (Responses API
// accounting) — they're tracked separately only so the UI can show the split.
export function useTokenCounter(initialInput = 0, initialOutput = 0, initialReasoning = 0) {
  const [inputTokens, setInputTokens] = useState(initialInput)
  const [outputTokens, setOutputTokens] = useState(initialOutput)
  const [reasoningTokens, setReasoningTokens] = useState(initialReasoning)

  const addUsage = useCallback((input, output, reasoning = 0) => {
    setInputTokens((v) => v + input)
    setOutputTokens((v) => v + output)
    setReasoningTokens((v) => v + reasoning)
  }, [])

  const reset = useCallback(() => {
    setInputTokens(0)
    setOutputTokens(0)
    setReasoningTokens(0)
  }, [])

  return { inputTokens, outputTokens, reasoningTokens, addUsage, reset }
}

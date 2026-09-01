export default function TokenCounter({ inputTokens, outputTokens, reasoningTokens = 0, parTokens }) {
  const total = inputTokens + outputTokens
  const ratio = parTokens ? (total / parTokens).toFixed(2) : '—'
  return (
    <div className="token-counter">
      <span>{total} tokens</span>
      <span className="par">/ {parTokens} par ({ratio}x)</span>
      {reasoningTokens > 0 && (
        <span
          className="thinking-tokens"
          title="Tokens the model spent thinking before answering. Already counted in the total — a tighter prompt shrinks this."
        >
          {reasoningTokens} thinking
        </span>
      )}
    </div>
  )
}

export default function TokenCounter({ inputTokens, outputTokens, parTokens }) {
  const total = inputTokens + outputTokens
  const ratio = parTokens ? (total / parTokens).toFixed(2) : '—'
  return (
    <div className="token-counter">
      <span>{total} tokens</span>
      <span className="par">/ {parTokens} par ({ratio}x)</span>
    </div>
  )
}

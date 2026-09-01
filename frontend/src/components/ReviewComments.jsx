// Renders inline `code` spans; the review prompt is told to use backticks
// for any suggested change so it doesn't need full Markdown.
function InlineText({ text }) {
  const parts = text.split(/(`[^`]+`)/g)
  return parts.map((part, i) =>
    part.startsWith('`') && part.endsWith('`') ? (
      <code key={i}>{part.slice(1, -1)}</code>
    ) : (
      part
    )
  )
}

export default function ReviewComments({ review }) {
  if (!review) return null
  const { time_complexity, space_complexity, comments } = review

  return (
    <div className="review-comments">
      <h3>AI review</h3>
      {(time_complexity || space_complexity) && (
        <div className="review-complexity">
          {time_complexity && (
            <div className="review-stat">
              <span className="review-stat-label">Time</span>
              <span className="review-stat-value">{time_complexity}</span>
            </div>
          )}
          {space_complexity && (
            <div className="review-stat">
              <span className="review-stat-label">Space</span>
              <span className="review-stat-value">{space_complexity}</span>
            </div>
          )}
        </div>
      )}
      {comments?.length > 0 && (
        <ul className="review-bullets">
          {comments.map((comment, i) => (
            <li key={i}>
              <InlineText text={comment} />
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

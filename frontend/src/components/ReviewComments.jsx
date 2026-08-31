export default function ReviewComments({ comments }) {
  if (!comments) return null
  return (
    <div className="review-comments">
      <h3>AI review</h3>
      <p>{comments}</p>
    </div>
  )
}

import { api, asProblemId } from '../lib/api'

// -> { comments }
export const postReview = (problemId, code) =>
  api('/review', {
    method: 'POST',
    body: JSON.stringify({ problem_id: asProblemId(problemId), code }),
  })

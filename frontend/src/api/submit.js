import { api, asProblemId } from '../lib/api'

// attemptId: the chat attempt the tested code came from, or null if the user
// hand-edited the code since the last chat reply (schemas.SubmitRequest).
// -> { passed, test_results, submission_id, attempt_id }
export const postSubmit = ({ problemId, code, inputTokens, outputTokens, elapsedSeconds, attemptId }) =>
  api('/submit', {
    method: 'POST',
    body: JSON.stringify({
      problem_id: asProblemId(problemId),
      code,
      input_tokens: inputTokens,
      output_tokens: outputTokens,
      elapsed_seconds: elapsedSeconds,
      attempt_id: attemptId ?? null,
    }),
  })

import { api, asProblemId } from '../lib/api'

// messageHistory: [{ role: 'user'|'assistant', content: string }]
// -> { reply, code, input_tokens, output_tokens, attempt_id }
export const postChat = (problemId, messageHistory) =>
  api('/chat', {
    method: 'POST',
    body: JSON.stringify({
      problem_id: asProblemId(problemId),
      message_history: messageHistory,
    }),
  })

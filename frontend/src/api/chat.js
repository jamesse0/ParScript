import { api, asProblemId } from '../lib/api'

// messageHistory: [{ role: 'user'|'assistant', content: string }]
// -> { reply, code, input_tokens, output_tokens, reasoning_tokens,
//      reasoning_summary, attempt_id }
// reasoning_tokens is part of output_tokens; reasoning_summary is a short gist
// of the model's thinking ('' if none).
export const postChat = (problemId, messageHistory) =>
  api('/chat', {
    method: 'POST',
    body: JSON.stringify({
      problem_id: asProblemId(problemId),
      message_history: messageHistory,
    }),
  })

import { api } from '../lib/api'

// mode: 'prompt' (token-ranked) or 'manual' (time-ranked). Default 'prompt'.
// -> LeaderboardRow[]: { username, user_id, submission_id, total_input_tokens,
//                        total_output_tokens, elapsed_seconds, created_at }
export const getLeaderboard = (problemId, mode = 'prompt') =>
  api(`/leaderboard/${problemId}?mode=${mode}`)

// The chat prompts behind one leaderboard score. 403 unless the caller has
// passed the same problem (or owns the score).
// -> { username, has_trace, prompts: string[], model, created_at }
export const getSubmissionPrompts = (submissionId) =>
  api(`/submissions/${submissionId}/prompts`)

// Ranked by handicap (avg tokens-vs-par ratio across solved problems, ascending).
// -> GlobalLeaderboardRow[]: { username, handicap, problems_solved }
export const getGlobalLeaderboard = () => api('/leaderboard/global')

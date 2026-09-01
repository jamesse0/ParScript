import { api } from '../lib/api'

// mode: 'prompt' (token-ranked) or 'manual' (time-ranked). Default 'prompt'.
// -> LeaderboardRow[]: { username, total_input_tokens, total_output_tokens, elapsed_seconds, created_at }
export const getLeaderboard = (problemId, mode = 'prompt') =>
  api(`/leaderboard/${problemId}?mode=${mode}`)

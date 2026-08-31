import { api } from '../lib/api'

// -> LeaderboardRow[]: { username, total_input_tokens, total_output_tokens, elapsed_seconds, created_at }
export const getLeaderboard = (problemId) => api(`/leaderboard/${problemId}`)

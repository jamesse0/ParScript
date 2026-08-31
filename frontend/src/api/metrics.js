import { api } from '../lib/api'

// -> MetricsResponse: { total_solved, avg_tokens_vs_par, avg_tokens_vs_par_by_difficulty, history }
export const getMetrics = () => api('/me/metrics')

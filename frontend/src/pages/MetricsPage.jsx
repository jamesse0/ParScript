import { useEffect, useState } from 'react'
import { getMetrics } from '../api/metrics'
import MetricsHistoryTable from '../components/MetricsHistoryTable'

export default function MetricsPage() {
  const [metrics, setMetrics] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getMetrics().then(setMetrics).catch((e) => setError(e.message))
  }, [])

  if (error) return <p className="error">{error}</p>
  if (!metrics) return <p>Loading...</p>

  return (
    <div className="metrics-page">
      <h1>Your metrics</h1>
      <div className="metrics-summary">
        <div>
          <span className="value">{metrics.total_solved}</span>
          <span className="label">problems solved</span>
        </div>
        <div>
          <span className="value">{metrics.avg_tokens_vs_par.toFixed(2)}x</span>
          <span className="label">avg tokens vs par</span>
        </div>
      </div>

      <h2>By difficulty</h2>
      <ul className="metrics-by-difficulty">
        {Object.entries(metrics.avg_tokens_vs_par_by_difficulty).map(([difficulty, ratio]) => (
          <li key={difficulty}>
            <span className={`tag tag-${difficulty}`}>{difficulty}</span>
            <span>{ratio.toFixed(2)}x par</span>
          </li>
        ))}
      </ul>

      <h2>History</h2>
      <MetricsHistoryTable rows={metrics.history} />
    </div>
  )
}

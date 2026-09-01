import { useEffect, useState } from 'react'
import { getGlobalLeaderboard } from '../api/leaderboard'
import GlobalLeaderboardTable from '../components/GlobalLeaderboardTable'

export default function GlobalLeaderboardPage() {
  const [rows, setRows] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getGlobalLeaderboard()
      .then(setRows)
      .catch((e) => setError(e.message))
  }, [])

  return (
    <div className="leaderboard-page">
      <h1>Global Leaderboard</h1>
      <p className="leaderboard-subtitle">
        Ranked by handicap: average tokens-vs-par ratio across each player's solved problems.
        Requires at least 3 solves to qualify.
      </p>
      {error && <p className="error">{error}</p>}
      {!rows && !error && <p>Loading...</p>}
      {rows && (rows.length ? <GlobalLeaderboardTable rows={rows} /> : <p>No qualifying players yet.</p>)}
    </div>
  )
}

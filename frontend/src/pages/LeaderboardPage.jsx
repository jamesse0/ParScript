import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getLeaderboard } from '../api/leaderboard'
import { getProblem } from '../api/problems'
import LeaderboardTable from '../components/LeaderboardTable'

export default function LeaderboardPage() {
  const { problemId } = useParams()
  const [problem, setProblem] = useState(null)
  const [rows, setRows] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([getProblem(problemId), getLeaderboard(problemId)])
      .then(([p, r]) => {
        setProblem(p)
        setRows(r)
      })
      .catch((e) => setError(e.message))
  }, [problemId])

  return (
    <div className="leaderboard-page">
      <Link to={`/problems/${problemId}`}>&larr; back to problem</Link>
      <h1>{problem ? problem.title : 'Leaderboard'}</h1>
      {error && <p className="error">{error}</p>}
      {!rows && !error && <p>Loading...</p>}
      {rows && (rows.length ? <LeaderboardTable rows={rows} /> : <p>No submissions yet.</p>)}
    </div>
  )
}

import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getLeaderboard } from '../api/leaderboard'
import { getProblem } from '../api/problems'
import LeaderboardTable from '../components/LeaderboardTable'
import ModeToggle from '../components/ModeToggle'

export default function LeaderboardPage() {
  const { problemId } = useParams()
  const [problem, setProblem] = useState(null)
  const [mode, setMode] = useState('prompt')
  const [rows, setRows] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getProblem(problemId)
      .then(setProblem)
      .catch((e) => setError(e.message))
  }, [problemId])

  useEffect(() => {
    setRows(null)
    getLeaderboard(problemId, mode)
      .then(setRows)
      .catch((e) => setError(e.message))
  }, [problemId, mode])

  return (
    <div className="leaderboard-page">
      <Link to={`/problems/${problemId}`}>&larr; back to problem</Link>
      <h1>{problem ? problem.title : 'Leaderboard'}</h1>
      <ModeToggle value={mode} onChange={setMode} />
      {error && <p className="error">{error}</p>}
      {!rows && !error && <p>Loading...</p>}
      {rows && (rows.length ? <LeaderboardTable rows={rows} mode={mode} /> : <p>No submissions yet.</p>)}
    </div>
  )
}

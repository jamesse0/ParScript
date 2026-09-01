import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getLeaderboard, getSubmissionPrompts } from '../api/leaderboard'
import { getProblem } from '../api/problems'
import LeaderboardTable from '../components/LeaderboardTable'
import ModeToggle from '../components/ModeToggle'
import PromptTrace from '../components/PromptTrace'

export default function LeaderboardPage() {
  const { problemId } = useParams()
  const [problem, setProblem] = useState(null)
  const [mode, setMode] = useState('prompt')
  const [rows, setRows] = useState(null)
  const [error, setError] = useState(null)
  const [trace, setTrace] = useState(null) // { open, loading, error, data }

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

  const openTrace = async (row) => {
    setTrace({ open: true, loading: true, error: null, data: null })
    try {
      const data = await getSubmissionPrompts(row.submission_id)
      setTrace({ open: true, loading: false, error: null, data })
    } catch (e) {
      const msg =
        e.status === 403
          ? "Submit a working solution to this problem to see other players' prompts."
          : e.message
      setTrace({ open: true, loading: false, error: msg, data: null })
    }
  }

  return (
    <div className="leaderboard-page">
      <Link to={`/problems/${problemId}`}>&larr; back to problem</Link>
      <h1>{problem ? problem.title : 'Leaderboard'}</h1>
      <ModeToggle value={mode} onChange={setMode} />
      {mode === 'prompt' && rows && rows.length > 0 && (
        <p className="muted">Click a row to see the prompts behind that score.</p>
      )}
      {error && <p className="error">{error}</p>}
      {!rows && !error && <p>Loading...</p>}
      {rows &&
        (rows.length ? (
          <LeaderboardTable
            rows={rows}
            mode={mode}
            onSelectRow={mode === 'prompt' ? openTrace : undefined}
          />
        ) : (
          <p>No submissions yet.</p>
        ))}

      <PromptTrace
        open={Boolean(trace?.open)}
        loading={Boolean(trace?.loading)}
        error={trace?.error}
        data={trace?.data}
        onClose={() => setTrace(null)}
      />
    </div>
  )
}

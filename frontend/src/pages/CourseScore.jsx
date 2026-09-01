import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getCourseLeaderboard } from '../api/courses'
import LeaderboardTable from '../components/LeaderboardTable'

// Shown by CourseRunnerPage once the final step is submitted.
//   completion: { total_input_tokens, total_output_tokens, elapsed_seconds, par_tokens, completed_at }
//   steps:      [{ submissionId, inputTokens, outputTokens, elapsedSeconds }] in course order
export default function CourseScore({ course, completion, steps, onRestart }) {
  const [rows, setRows] = useState(null)

  useEffect(() => {
    getCourseLeaderboard(course.slug)
      .then((r) => setRows(r.slice(0, 5)))
      .catch(() => setRows([]))
  }, [course.slug])

  const total = completion.total_input_tokens + completion.total_output_tokens
  const par = completion.par_tokens
  const ratio = par ? total / par : null

  return (
    <div className="course-score">
      <h1>{course.title} — complete</h1>

      <div className="course-score-headline">
        <span className="course-score-total">{total.toLocaleString()}</span>
        <span className="course-score-sub">total tokens across {course.steps.length} steps</span>
        {ratio != null && (
          <span className={`course-score-ratio ${ratio <= 1 ? 'under' : 'over'}`}>
            {ratio.toFixed(2)}× par ({par.toLocaleString()})
          </span>
        )}
      </div>

      <table className="course-score-breakdown">
        <thead>
          <tr>
            <th>Step</th>
            <th>Input</th>
            <th>Output</th>
            <th>Tokens</th>
            <th>Time</th>
          </tr>
        </thead>
        <tbody>
          {course.steps.map((s, i) => {
            const d = steps[i] ?? { inputTokens: 0, outputTokens: 0, elapsedSeconds: 0 }
            return (
              <tr key={s.problem_id}>
                <td>{s.title}</td>
                <td>{d.inputTokens.toLocaleString()}</td>
                <td>{d.outputTokens.toLocaleString()}</td>
                <td>{(d.inputTokens + d.outputTokens).toLocaleString()}</td>
                <td>{d.elapsedSeconds.toFixed(1)}s</td>
              </tr>
            )
          })}
        </tbody>
      </table>

      <div className="course-score-leaderboard">
        <div className="course-score-leaderboard-head">
          <h2>Course leaderboard</h2>
          <Link to={`/courses/${course.slug}/leaderboard`}>Full leaderboard &rarr;</Link>
        </div>
        {!rows && <p>Loading...</p>}
        {rows &&
          (rows.length ? (
            <LeaderboardTable rows={rows} mode="prompt" />
          ) : (
            <p>No completions yet.</p>
          ))}
      </div>

      <div className="course-score-actions">
        <button className="btn btn-outline" onClick={onRestart}>
          Restart course
        </button>
        <Link to="/courses" className="btn btn-accent">
          Back to courses
        </Link>
      </div>
    </div>
  )
}

import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getCourse, getCourseLeaderboard } from '../api/courses'
import LeaderboardTable from '../components/LeaderboardTable'

export default function CourseLeaderboardPage() {
  const { courseSlug } = useParams()
  const [course, setCourse] = useState(null)
  const [rows, setRows] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getCourse(courseSlug)
      .then(setCourse)
      .catch((e) => setError(e.message))
  }, [courseSlug])

  useEffect(() => {
    getCourseLeaderboard(courseSlug)
      .then(setRows)
      .catch((e) => setError(e.message))
  }, [courseSlug])

  return (
    <div className="leaderboard-page">
      <Link to="/courses">&larr; back to courses</Link>
      <h1>{course ? course.title : 'Course'} — leaderboard</h1>
      <p className="muted">
        Ranked by total tokens across {course ? `all ${course.step_count}` : 'every'} steps.
      </p>
      {error && <p className="error">{error}</p>}
      {!rows && !error && <p>Loading...</p>}
      {rows &&
        (rows.length ? (
          <LeaderboardTable rows={rows} mode="prompt" />
        ) : (
          <p>No completions yet.</p>
        ))}
    </div>
  )
}

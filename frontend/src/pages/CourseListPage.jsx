import { useEffect, useState } from 'react'
import { getCourses } from '../api/courses'
import CourseCard from '../components/CourseCard'

export default function CourseListPage() {
  const [courses, setCourses] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    getCourses()
      .then(setCourses)
      .catch((e) => setError(e.message))
  }, [])

  return (
    <div className="problem-list-page">
      <h1>Courses</h1>
      <p className="muted">
        Multi-step sequences: the code you submit for each step pre-fills the next one. Your
        course score is the total tokens across every step — maintainable code keeps it low.
      </p>
      {error && <p className="error">{error}</p>}
      {!courses && !error && <p>Loading...</p>}
      {courses && courses.length === 0 && <p>No courses yet.</p>}
      <div className="problem-grid">
        {courses?.map((c) => (
          <CourseCard key={c.slug} course={c} />
        ))}
      </div>
    </div>
  )
}

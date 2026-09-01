import { Link } from 'react-router-dom'

export default function CourseCard({ course }) {
  return (
    <div className="problem-card course-card">
      <h3 className="problem-card-title">{course.title}</h3>
      <p className="course-card-desc">{course.description}</p>
      <div className="problem-card-footer">
        <div className="problem-card-meta">
          <span className="difficulty-badge difficulty-system_design">Course</span>
          <span className="par-tokens">
            {course.step_count} steps · {course.par_tokens} par
          </span>
        </div>
        <Link to={`/courses/${course.slug}`} className="btn btn-accent">
          Start
        </Link>
      </div>
    </div>
  )
}

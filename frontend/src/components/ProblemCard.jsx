import { Link } from 'react-router-dom'

export default function ProblemCard({ problem }) {
  return (
    <div className="problem-card">
      <h3 className="problem-card-title">{problem.title}</h3>
      <div className="problem-card-footer">
        <div className="problem-card-meta">
          <span className={`difficulty-badge difficulty-${problem.difficulty}`}>
            {problem.difficulty}
          </span>
          <span className="par-tokens">{problem.par_tokens} par</span>
        </div>
        <Link to={`/problems/${problem.id}`} className="btn btn-accent">
          Start
        </Link>
      </div>
    </div>
  )
}

import { Link } from 'react-router-dom'

export default function ProblemCard({ problem }) {
  return (
    <Link to={`/problems/${problem.id}`} className="problem-card">
      <h3>{problem.title}</h3>
      <span className={`tag tag-${problem.difficulty}`}>{problem.difficulty}</span>
      <span className="par">par: {problem.par_tokens} tokens</span>
    </Link>
  )
}

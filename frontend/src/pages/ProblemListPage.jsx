import { useEffect, useState } from 'react'
import { getProblems } from '../api/problems'
import ProblemCard from '../components/ProblemCard'
import DifficultyFilter from '../components/DifficultyFilter'

export default function ProblemListPage() {
  const [difficulty, setDifficulty] = useState('all')
  const [problems, setProblems] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    setProblems(null)
    getProblems(difficulty === 'all' ? undefined : difficulty)
      .then(setProblems)
      .catch((e) => setError(e.message))
  }, [difficulty])

  return (
    <div className="problem-list-page">
      <h1>Problems</h1>
      <DifficultyFilter value={difficulty} onChange={setDifficulty} />
      {error && <p className="error">{error}</p>}
      {!problems && !error && <p>Loading...</p>}
      <div className="problem-grid">
        {problems?.map((p) => (
          <ProblemCard key={p.id} problem={p} />
        ))}
      </div>
    </div>
  )
}

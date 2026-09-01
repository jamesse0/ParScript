import { difficultyLabel } from '../lib/difficulty'

const OPTIONS = ['all', 'easy', 'medium', 'hard', 'system_design']

export default function DifficultyFilter({ value, onChange }) {
  return (
    <div className="difficulty-filter">
      {OPTIONS.map((opt) => (
        <button
          key={opt}
          className={value === opt ? 'active' : ''}
          onClick={() => onChange(opt)}
        >
          {opt === 'all' ? 'all' : difficultyLabel(opt)}
        </button>
      ))}
    </div>
  )
}

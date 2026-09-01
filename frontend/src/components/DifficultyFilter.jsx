const OPTIONS = ['all', 'easy', 'medium', 'hard', 'system_design']
const LABELS = { system_design: 'system design' }

export default function DifficultyFilter({ value, onChange }) {
  return (
    <div className="difficulty-filter">
      {OPTIONS.map((opt) => (
        <button
          key={opt}
          className={value === opt ? 'active' : ''}
          onClick={() => onChange(opt)}
        >
          {LABELS[opt] ?? opt}
        </button>
      ))}
    </div>
  )
}

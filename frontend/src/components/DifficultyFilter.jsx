const OPTIONS = ['all', 'easy', 'medium', 'hard']

export default function DifficultyFilter({ value, onChange }) {
  return (
    <div className="difficulty-filter">
      {OPTIONS.map((opt) => (
        <button
          key={opt}
          className={value === opt ? 'active' : ''}
          onClick={() => onChange(opt)}
        >
          {opt}
        </button>
      ))}
    </div>
  )
}

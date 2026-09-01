const OPTIONS = [
  { value: 'prompt', label: 'Prompt Engineering' },
  { value: 'manual', label: 'Manual' },
]

// Segmented control for the workspace / leaderboard mode.
// Reuses the .difficulty-filter pill-button styling.
export default function ModeToggle({ value, onChange }) {
  return (
    <div className="difficulty-filter mode-toggle">
      {OPTIONS.map((opt) => (
        <button
          key={opt.value}
          className={value === opt.value ? 'active' : ''}
          onClick={() => onChange(opt.value)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  )
}

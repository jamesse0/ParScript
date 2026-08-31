export default function CodePanel({ code, onChange }) {
  return (
    <div className="code-panel">
      <textarea
        className="code-editor"
        value={code}
        onChange={(e) => onChange(e.target.value)}
        spellCheck={false}
        rows={20}
      />
    </div>
  )
}

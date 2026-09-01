export default function CodePanel({ code }) {
  return (
    <div className="code-panel">
      <textarea
        className="code-editor"
        value={code}
        readOnly
        spellCheck={false}
        rows={12}
      />
    </div>
  )
}

import { useLayoutEffect, useRef } from 'react'

export default function CodePanel({ code, onChange }) {
  const textareaRef = useRef(null)

  useLayoutEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${el.scrollHeight}px`
  }, [code])

  return (
    <div className="code-panel">
      <textarea
        ref={textareaRef}
        className="code-editor"
        value={code}
        onChange={(e) => onChange(e.target.value)}
        spellCheck={false}
        rows={12}
      />
    </div>
  )
}

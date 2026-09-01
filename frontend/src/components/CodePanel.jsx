import { useLayoutEffect, useRef } from 'react'

const INDENT = '\t' // one real tab char -- one keystroke to add or delete

// Code box. Editable in Manual mode (auto-grows, Tab/Shift+Tab/Enter do
// sensible indentation instead of browser defaults); read-only in Prompt
// mode, where the code is AI-generated and shouldn't be hand-edited.
export default function CodePanel({ code, onChange, readOnly = false }) {
  const textareaRef = useRef(null)

  useLayoutEffect(() => {
    const el = textareaRef.current
    if (!el) return
    el.style.height = 'auto'
    el.style.height = `${el.scrollHeight}px`
  }, [code])

  const putCaret = (start, end = start) => {
    requestAnimationFrame(() => {
      const el = textareaRef.current
      if (el) el.setSelectionRange(start, end)
    })
  }

  const handleKeyDown = (e) => {
    if (readOnly) return
    const { selectionStart: start, selectionEnd: end } = e.target

    // Enter: start the new line at the same indent (one deeper after a ":")
    if (e.key === 'Enter' && start === end) {
      e.preventDefault()
      const lineStart = code.lastIndexOf('\n', start - 1) + 1
      const lineToCaret = code.slice(lineStart, start)
      let indent = lineToCaret.match(/^[ \t]*/)[0]
      if (/:\s*$/.test(lineToCaret)) indent += INDENT
      const insert = '\n' + indent
      onChange(code.slice(0, start) + insert + code.slice(end))
      putCaret(start + insert.length)
      return
    }

    if (e.key !== 'Tab') return
    e.preventDefault()

    // plain caret, no selection: insert one indent
    if (!e.shiftKey && start === end) {
      onChange(code.slice(0, start) + INDENT + code.slice(start))
      putCaret(start + INDENT.length)
      return
    }

    // selection (or Shift+Tab): indent / dedent every line it touches
    const lineStart = code.lastIndexOf('\n', start - 1) + 1
    const region = code.slice(lineStart, end)
    const newRegion = e.shiftKey
      ? region.replace(/^(\t| {1,4})/gm, '') // drop a leading tab, or up to 4 spaces
      : region.replace(/^(?!$)/gm, INDENT)
    onChange(code.slice(0, lineStart) + newRegion + code.slice(end))
    putCaret(lineStart, lineStart + newRegion.length)
  }

  return (
    <div className="code-panel">
      <textarea
        ref={textareaRef}
        className="code-editor"
        value={code}
        onChange={(e) => !readOnly && onChange(e.target.value)}
        onKeyDown={handleKeyDown}
        readOnly={readOnly}
        spellCheck={false}
        wrap="off"
        rows={12}
      />
    </div>
  )
}

import { useEffect } from 'react'
import Markdown from './Markdown'

// Read-only viewer for the chat prompts behind a leaderboard score. The point
// is to learn from how someone phrased things, not to paste it -- so the list
// is not selectable and copy / cut / right-click / drag are all blocked.
export default function PromptTrace({ open, loading, error, data, onClose }) {
  useEffect(() => {
    if (!open) return undefined
    const onKey = (e) => e.key === 'Escape' && onClose()
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [open, onClose])

  if (!open) return null

  const block = (e) => e.preventDefault()

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal prompt-trace" onClick={(e) => e.stopPropagation()}>
        <button className="modal-close" onClick={onClose} aria-label="Close">
          &times;
        </button>

        {loading && <p>Loading…</p>}
        {error && <p className="error">{error}</p>}

        {data && (
          <>
            <h2 className="prompt-trace-title">{data.username}&rsquo;s prompts</h2>
            {!data.has_trace ? (
              <p className="muted">
                No chat was recorded for this run &mdash; it was hand-written or edited directly.
              </p>
            ) : (
              <ol
                className="prompt-trace-list no-copy"
                onCopy={block}
                onCut={block}
                onContextMenu={block}
                onDragStart={block}
              >
                {data.prompts.map((p, i) => (
                  <li key={i}>
                    <Markdown text={p} />
                  </li>
                ))}
              </ol>
            )}
            {data.model && <p className="muted prompt-trace-meta">via {data.model}</p>}
          </>
        )}
      </div>
    </div>
  )
}

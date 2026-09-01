import { useEffect, useState } from 'react'

export default function ChatPanel({ messages, onSend, sending, resetSignal }) {
  const [draft, setDraft] = useState('')
  const [openReplies, setOpenReplies] = useState(() => new Set())

  useEffect(() => {
    setDraft('')
    setOpenReplies(new Set())
  }, [resetSignal])

  const send = (e) => {
    e.preventDefault()
    if (!draft.trim() || sending) return
    onSend(draft.trim())
    setDraft('')
  }

  const toggleReply = (i) => {
    setOpenReplies((open) => {
      const next = new Set(open)
      if (next.has(i)) next.delete(i)
      else next.add(i)
      return next
    })
  }

  return (
    <div className="chat-panel">
      <div className="chat-messages">
        {messages.map((m, i) =>
          m.role === 'assistant' ? (
            <div key={i} className="chat-message chat-assistant">
              <button type="button" className="chat-reply-toggle" onClick={() => toggleReply(i)}>
                {openReplies.has(i) ? '▾' : '▸'} Show prompt response
              </button>
              {openReplies.has(i) && <p>{m.content}</p>}
            </div>
          ) : (
            <div key={i} className="chat-message chat-user">
              <strong>{m.role}</strong>
              <p>{m.content}</p>
            </div>
          )
        )}
        {sending && <p className="chat-pending">thinking…</p>}
      </div>
      <form onSubmit={send} className="chat-input">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Describe the approach or ask for a fix..."
          rows={7}
        />
        <button type="submit" className="btn btn-accent" disabled={sending || !draft.trim()}>
          Send
        </button>
      </form>
    </div>
  )
}

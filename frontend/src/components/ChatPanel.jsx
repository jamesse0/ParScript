import { useState } from 'react'

export default function ChatPanel({ messages, onSend, sending }) {
  const [draft, setDraft] = useState('')

  const send = (e) => {
    e.preventDefault()
    if (!draft.trim() || sending) return
    onSend(draft.trim())
    setDraft('')
  }

  return (
    <div className="chat-panel">
      <div className="chat-messages">
        {messages.map((m, i) => (
          <div key={i} className={`chat-message chat-${m.role}`}>
            <strong>{m.role}</strong>
            <p>{m.content}</p>
          </div>
        ))}
        {sending && <p className="chat-pending">thinking…</p>}
      </div>
      <form onSubmit={send} className="chat-input">
        <textarea
          value={draft}
          onChange={(e) => setDraft(e.target.value)}
          placeholder="Describe the approach or ask for a fix..."
          rows={3}
        />
        <button type="submit" disabled={sending || !draft.trim()}>
          Send
        </button>
      </form>
    </div>
  )
}

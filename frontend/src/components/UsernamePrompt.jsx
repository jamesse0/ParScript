import { useState } from 'react'

export default function UsernamePrompt({ onSubmit }) {
  const [username, setUsername] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const submit = async (e) => {
    e.preventDefault()
    setError(null)
    setBusy(true)
    try {
      await onSubmit(username.trim())
    } catch (err) {
      if (err.status === 409) setError('That username is taken')
      else if (err.status === 422) setError('3–30 chars: letters, digits, underscores')
      else setError('Something went wrong, try again')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="username-prompt">
      <h2>Choose a username</h2>
      <p>This is what shows up on leaderboards.</p>
      <form onSubmit={submit}>
        <input
          value={username}
          onChange={(e) => setUsername(e.target.value)}
          placeholder="username"
          minLength={3}
          maxLength={30}
          required
        />
        <button type="submit" disabled={busy || username.trim().length < 3}>
          Continue
        </button>
      </form>
      {error && <p className="error">{error}</p>}
    </div>
  )
}

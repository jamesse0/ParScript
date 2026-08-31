import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getMetrics } from '../api/metrics'
import { getMe } from '../api/profile'
import { signOut } from '../lib/AuthProvider'
import MetricsHistoryTable from '../components/MetricsHistoryTable'

export default function ProfilePage() {
  const [profile, setProfile] = useState(null)
  const [metrics, setMetrics] = useState(null)
  const [error, setError] = useState(null)
  const [signingOut, setSigningOut] = useState(false)
  const navigate = useNavigate()

  useEffect(() => {
    getMe().then(setProfile).catch((e) => setError(e.message))
    getMetrics().then(setMetrics).catch((e) => setError(e.message))
  }, [])

  const handleSignOut = async () => {
    setSigningOut(true)
    await signOut()
    navigate('/login', { replace: true })
  }

  if (error) return <p className="error">{error}</p>
  if (!metrics || !profile) return <p>Loading...</p>

  return (
    <div className="profile-page">
      <div className="profile-header">
        <div>
          <h1>{profile.username}</h1>
          <p className="profile-meta">
            Member since {new Date(profile.created_at).toLocaleDateString()}
          </p>
        </div>
        <button className="btn btn-outline" onClick={handleSignOut} disabled={signingOut}>
          {signingOut ? 'Signing out...' : 'Log out'}
        </button>
      </div>

      <div className="metrics-summary">
        <div>
          <span className="value">{metrics.total_solved}</span>
          <span className="label">problems solved</span>
        </div>
        <div>
          <span className="value">{metrics.avg_tokens_vs_par.toFixed(2)}x</span>
          <span className="label">avg tokens vs par</span>
        </div>
      </div>

      <h2>By difficulty</h2>
      <ul className="metrics-by-difficulty">
        {Object.entries(metrics.avg_tokens_vs_par_by_difficulty).map(([difficulty, ratio]) => (
          <li key={difficulty}>
            <span className={`tag tag-${difficulty}`}>{difficulty}</span>
            <span>{ratio.toFixed(2)}x par</span>
          </li>
        ))}
      </ul>

      <h2>History</h2>
      <MetricsHistoryTable rows={metrics.history} />
    </div>
  )
}

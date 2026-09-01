import { Navigate } from 'react-router-dom'
import { useAuth } from '../lib/AuthProvider'
import GithubButton from '../components/GithubButton'

export default function LoginPage() {
  const { session, loading } = useAuth()
  if (loading) return <p>Loading...</p>
  if (session) return <Navigate to="/problems" replace />

  return (
    <div className="login-page">
      <h1>Par Prompt</h1>
      <p>Solve algorithm problems by prompting an AI — scored on token efficiency.</p>
      <GithubButton />
    </div>
  )
}

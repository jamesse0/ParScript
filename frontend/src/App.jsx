import { Routes, Route, Navigate, Link } from 'react-router-dom'
import RequireAuth from './components/RequireAuth'
import OnboardingGate from './components/OnboardingGate'
import LoginPage from './pages/LoginPage'
import ProblemListPage from './pages/ProblemListPage'
import ProblemWorkspacePage from './pages/ProblemWorkspacePage'
import LeaderboardPage from './pages/LeaderboardPage'
import ProfilePage from './pages/ProfilePage'

export default function App() {
  return (
    <>
      <nav className="app-nav">
        <Link to="/problems">Problems</Link>
        <Link to="/profile">Profile</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Navigate to="/problems" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/problems" element={<ProblemListPage />} />
        <Route path="/problems/:problemId/leaderboard" element={<LeaderboardPage />} />
        <Route
          path="/problems/:problemId"
          element={
            <RequireAuth>
              <OnboardingGate>
                <ProblemWorkspacePage />
              </OnboardingGate>
            </RequireAuth>
          }
        />
        <Route
          path="/profile"
          element={
            <RequireAuth>
              <OnboardingGate>
                <ProfilePage />
              </OnboardingGate>
            </RequireAuth>
          }
        />
      </Routes>
    </>
  )
}

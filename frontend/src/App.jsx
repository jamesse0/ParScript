import { Routes, Route, Navigate, Link, NavLink } from 'react-router-dom'
import RequireAuth from './components/RequireAuth'
import OnboardingGate from './components/OnboardingGate'
import LoginPage from './pages/LoginPage'
import ProblemListPage from './pages/ProblemListPage'
import ProblemWorkspacePage from './pages/ProblemWorkspacePage'
import LeaderboardPage from './pages/LeaderboardPage'
import GlobalLeaderboardPage from './pages/GlobalLeaderboardPage'
import ProfilePage from './pages/ProfilePage'
import logo from './assets/parprompt-logo.png'

export default function App() {
  return (
    <>
      <nav className="app-nav">
        <Link to="/problems" className="brand">
          <img src={logo} alt="Par Prompt" className="brand-logo" />
        </Link>
        <div className="nav-links">
          <NavLink to="/problems" className={({ isActive }) => (isActive ? 'active' : undefined)}>
            Problems
          </NavLink>
          <NavLink to="/leaderboard" className={({ isActive }) => (isActive ? 'active' : undefined)}>
            Leaderboard
          </NavLink>
          <NavLink to="/profile" className={({ isActive }) => (isActive ? 'active' : undefined)}>
            Profile
          </NavLink>
        </div>
      </nav>
      <Routes>
        <Route path="/" element={<Navigate to="/problems" replace />} />
        <Route path="/login" element={<LoginPage />} />
        <Route path="/problems" element={<ProblemListPage />} />
        <Route path="/leaderboard" element={<GlobalLeaderboardPage />} />
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

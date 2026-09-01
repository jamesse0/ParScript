import { Routes, Route, Link, NavLink } from 'react-router-dom'
import RequireAuth from './components/RequireAuth'
import OnboardingGate from './components/OnboardingGate'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import ProblemListPage from './pages/ProblemListPage'
import ProblemWorkspacePage from './pages/ProblemWorkspacePage'
import CourseListPage from './pages/CourseListPage'
import CourseRunnerPage from './pages/CourseRunnerPage'
import CourseLeaderboardPage from './pages/CourseLeaderboardPage'
import LeaderboardPage from './pages/LeaderboardPage'
import GlobalLeaderboardPage from './pages/GlobalLeaderboardPage'
import ProfilePage from './pages/ProfilePage'
import logo from './assets/parprompt-logo.png'

export default function App() {
  return (
    <div className="app-shell">
      <nav className="app-nav">
        <Link to="/" className="brand">
          <img src={logo} alt="Par Prompt" className="brand-logo" />
        </Link>
        <div className="nav-links">
          <NavLink to="/problems" className={({ isActive }) => (isActive ? 'active' : undefined)}>
            Problems
          </NavLink>
          <NavLink to="/courses" className={({ isActive }) => (isActive ? 'active' : undefined)}>
            Courses
          </NavLink>
          <NavLink to="/leaderboard" className={({ isActive }) => (isActive ? 'active' : undefined)}>
            Leaderboard
          </NavLink>
          <NavLink to="/profile" className={({ isActive }) => (isActive ? 'active' : undefined)}>
            Profile
          </NavLink>
        </div>
      </nav>
      <main className="app-main">
        <Routes>
          <Route path="/" element={<HomePage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/problems" element={<ProblemListPage />} />
          <Route path="/courses" element={<CourseListPage />} />
          <Route path="/courses/:courseSlug/leaderboard" element={<CourseLeaderboardPage />} />
          <Route
            path="/courses/:courseSlug"
            element={
              <RequireAuth>
                <OnboardingGate>
                  <CourseRunnerPage />
                </OnboardingGate>
              </RequireAuth>
            }
          />
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
      </main>
    </div>
  )
}

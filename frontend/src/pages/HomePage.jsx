import { useEffect, useRef, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../lib/AuthProvider'
import GithubButton from '../components/GithubButton'
import { getMe } from '../api/profile'
import { getMetrics } from '../api/metrics'
import { getGlobalLeaderboard } from '../api/leaderboard'
import logo from '../assets/parprompt-logo.png'

const SLIDES = [
  {
    title: 'Welcome to Par Prompt',
    body: "Practice writing efficient prompts and hit par on every problem.",
  },
  {
    title: 'New: System Design Round',
    body: 'Hidden pytest-graded system design problems just dropped in the course list.',
  },
  {
    title: 'Track Your Handicap',
    body: "See how your average tokens-vs-par ratio stacks up on the global leaderboard.",
  },
  {
    title: 'Prefer to Type It Yourself?',
    body: 'Switch to Manual mode on any problem and race the clock instead of the model.',
  },
]

const SLIDE_INTERVAL_MS = 5000

function Carousel() {
  const [index, setIndex] = useState(0)
  const timerRef = useRef(null)

  const restartTimer = () => {
    clearInterval(timerRef.current)
    timerRef.current = setInterval(() => {
      setIndex((i) => (i + 1) % SLIDES.length)
    }, SLIDE_INTERVAL_MS)
  }

  useEffect(() => {
    restartTimer()
    return () => clearInterval(timerRef.current)
  }, [])

  const goTo = (i) => {
    setIndex(i)
    restartTimer()
  }

  return (
    <div className="home-carousel">
      <div className="home-carousel-track" style={{ transform: `translateX(-${index * 100}%)` }}>
        {SLIDES.map((slide, i) => (
          <div className="home-slide" key={i}>
            <h2>{slide.title}</h2>
            <p>{slide.body}</p>
          </div>
        ))}
      </div>
      <div className="home-carousel-dots">
        {SLIDES.map((_, i) => (
          <button
            key={i}
            className={i === index ? 'active' : ''}
            aria-label={`Go to slide ${i + 1}`}
            onClick={() => goTo(i)}
          />
        ))}
      </div>
    </div>
  )
}

function AccountTile() {
  const { session } = useAuth()
  const [profile, setProfile] = useState(null)
  const [metrics, setMetrics] = useState(null)

  useEffect(() => {
    if (!session) return
    getMe().then(setProfile).catch(() => {})
    getMetrics().then(setMetrics).catch(() => {})
  }, [session])

  if (!session) {
    return (
      <div className="home-tile home-account-tile">
        <h3>Create an Account</h3>
        <p>Sign in with GitHub to start tracking your par.</p>
        <GithubButton />
      </div>
    )
  }

  return (
    <Link to="/profile" className="home-tile home-account-tile home-tile-link">
      <h3>{profile?.username ?? 'Loading...'}</h3>
      <div className="home-stat">
        <span className="home-stat-value">
          {metrics ? `${metrics.avg_tokens_vs_par.toFixed(2)}x` : '—'}
        </span>
        <span className="home-stat-label">avg tokens vs par</span>
      </div>
    </Link>
  )
}

function LeaderboardTile() {
  const [rows, setRows] = useState(null)

  useEffect(() => {
    getGlobalLeaderboard()
      .then((r) => setRows(r.slice(0, 5)))
      .catch(() => setRows([]))
  }, [])

  return (
    <Link to="/leaderboard" className="home-tile home-leaderboard-tile home-tile-link">
      <h3>Top 5</h3>
      {!rows && <p className="home-tile-empty">Loading...</p>}
      {rows && rows.length === 0 && <p className="home-tile-empty">No qualifying players yet.</p>}
      {rows && rows.length > 0 && (
        <ol className="home-leaderboard-list">
          {rows.map((row, i) => (
            <li key={i}>
              <span className="home-rank">{i + 1}</span>
              <span className="home-username">{row.username}</span>
              <span className="home-handicap">{row.handicap.toFixed(2)}</span>
            </li>
          ))}
        </ol>
      )}
    </Link>
  )
}

export default function HomePage() {
  return (
    <div className="home-page">
      <section className="home-splash">
        <div className="home-splash-bg" />
        <div className="home-splash-scrim" />

        <div className="home-splash-content">
          <div className="home-splash-logo-badge">
            <img src={logo} alt="Par Prompt" className="home-splash-logo" />
          </div>
          <div className="home-splash-copy">
            <p className="home-splash-slogan">Efficiency is the new green.</p>
            <p className="home-splash-vision">
              Treating efficient prompting as practice rewards fewer tokens, faster answers, and a
              smaller footprint behind every idea.
            </p>
          </div>
        </div>

        <div className="home-scroll-cue" aria-hidden="true">
          <span>Scroll</span>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M6 9l6 6 6-6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </div>
      </section>

      <section className="home-hero-section">
        <div className="home-hero">
          <Carousel />
          <div className="home-side-tiles">
            <AccountTile />
            <LeaderboardTile />
          </div>
        </div>
        <Link to="/problems" className="home-cta">
          View Problems
        </Link>
      </section>
    </div>
  )
}

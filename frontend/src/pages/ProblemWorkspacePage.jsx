import { useEffect, useRef, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getProblem } from '../api/problems'
import { postChat } from '../api/chat'
import { postSubmit } from '../api/submit'
import { postReview } from '../api/review'
import { getLeaderboard } from '../api/leaderboard'
import { useTokenCounter } from '../hooks/useTokenCounter'
import { useElapsedTimer } from '../hooks/useElapsedTimer'
import { loadWorkspaceState, saveWorkspaceState, clearWorkspaceState } from '../lib/workspaceStorage'
import ChatPanel from '../components/ChatPanel'
import CodePanel from '../components/CodePanel'
import TokenCounter from '../components/TokenCounter'
import Timer from '../components/Timer'
import TestResultsList from '../components/TestResultsList'
import ReviewComments from '../components/ReviewComments'
import LeaderboardTable from '../components/LeaderboardTable'
import ModeToggle from '../components/ModeToggle'
import ProblemDescription from '../components/ProblemDescription'

const SIDEBAR_WIDTH_KEY = 'parscript:sidebarWidth'
const MIN_SIDEBAR_WIDTH = 280
const MAX_SIDEBAR_WIDTH = 900
const DEFAULT_SIDEBAR_WIDTH = 340

function loadSidebarWidth() {
  try {
    const stored = Number(localStorage.getItem(SIDEBAR_WIDTH_KEY))
    if (stored >= MIN_SIDEBAR_WIDTH && stored <= MAX_SIDEBAR_WIDTH) return stored
  } catch {
    // storage disabled -- fall through to default
  }
  return DEFAULT_SIDEBAR_WIDTH
}

export default function ProblemWorkspacePage() {
  const { problemId } = useParams()
  const [problem, setProblem] = useState(null)
  const [error, setError] = useState(null)

  const [saved] = useState(() => loadWorkspaceState(problemId))

  // 'prompt' = chat with the AI; 'manual' = hand-write the solution, ranked by time.
  const [mode, setMode] = useState(saved?.mode ?? 'prompt')

  const [sidebarWidth, setSidebarWidth] = useState(loadSidebarWidth)
  const [resizingSidebar, setResizingSidebar] = useState(false)

  const handleResizeStart = (e) => {
    e.preventDefault()
    const startX = e.clientX
    const startWidth = sidebarWidth
    setResizingSidebar(true)

    const onMouseMove = (moveEvent) => {
      const next = Math.min(
        MAX_SIDEBAR_WIDTH,
        Math.max(MIN_SIDEBAR_WIDTH, startWidth + moveEvent.clientX - startX)
      )
      setSidebarWidth(next)
    }
    const onMouseUp = () => {
      window.removeEventListener('mousemove', onMouseMove)
      window.removeEventListener('mouseup', onMouseUp)
      setResizingSidebar(false)
      setSidebarWidth((width) => {
        try {
          localStorage.setItem(SIDEBAR_WIDTH_KEY, String(width))
        } catch {
          // storage disabled -- resize still works for this session
        }
        return width
      })
    }

    window.addEventListener('mousemove', onMouseMove)
    window.addEventListener('mouseup', onMouseUp)
  }

  const [messages, setMessages] = useState(saved?.messages ?? [])
  const [code, setCode] = useState(saved?.code ?? '')
  const [lastAttemptId, setLastAttemptId] = useState(saved?.lastAttemptId ?? null)
  const [sending, setSending] = useState(false)

  const [submitting, setSubmitting] = useState(false)
  const [testResults, setTestResults] = useState(saved?.testResults ?? null)
  const [passed, setPassed] = useState(saved?.passed ?? false)
  const [reviewComments, setReviewComments] = useState(saved?.reviewComments ?? null)
  const [submitError, setSubmitError] = useState(null)

  const [leaderboard, setLeaderboard] = useState(null)
  const [leaderboardError, setLeaderboardError] = useState(null)

  const attemptRef = useRef(0)
  const reviewRef = useRef(null)

  const { inputTokens, outputTokens, addUsage, reset: resetTokens } = useTokenCounter(saved?.inputTokens, saved?.outputTokens)
  const {
    elapsedSeconds,
    start,
    stop: stopTimer,
    currentElapsedSeconds,
    startedAt,
    reset: resetTimer,
  } = useElapsedTimer(saved?.startedAt, !saved?.passed, saved?.elapsedSeconds)

  useEffect(() => {
    getProblem(problemId)
      .then((p) => {
        setProblem(p)
        if (saved?.code === undefined) {
          setCode(p.starter_code)
        }
      })
      .catch((e) => setError(e.message))
  }, [problemId, saved])

  // Manual mode: the clock runs from the moment the page is ready, not from a
  // first chat message. start() is idempotent, so re-running is harmless.
  useEffect(() => {
    if (problem && mode === 'manual' && !passed) start()
  }, [problem, mode, passed, start])

  useEffect(() => {
    saveWorkspaceState(problemId, {
      mode,
      messages,
      code,
      lastAttemptId,
      testResults,
      passed,
      reviewComments,
      inputTokens,
      outputTokens,
      startedAt,
      elapsedSeconds,
    })
  }, [
    problemId,
    mode,
    messages,
    code,
    lastAttemptId,
    testResults,
    passed,
    reviewComments,
    inputTokens,
    outputTokens,
    startedAt,
    elapsedSeconds,
  ])

  const refreshLeaderboard = () => {
    // The sidebar widget always shows the AI (prompt) leaderboard.
    getLeaderboard(problemId, 'prompt')
      .then((rows) => {
        setLeaderboard(rows)
        setLeaderboardError(null)
      })
      .catch((e) => setLeaderboardError(e.message))
  }

  useEffect(() => {
    refreshLeaderboard()
  }, [problemId])

  useEffect(() => {
    if (reviewComments) {
      reviewRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [reviewComments])

  const resetSession = () => {
    attemptRef.current += 1
    clearWorkspaceState(problemId)
    setMessages([])
    setCode(problem.starter_code)
    setLastAttemptId(null)
    setSending(false)
    setSubmitting(false)
    setTestResults(null)
    setPassed(false)
    setReviewComments(null)
    setSubmitError(null)
    resetTokens()
    resetTimer()
  }

  const handleReplay = () => {
    resetSession()
  }

  const handleModeChange = (next) => {
    if (next === mode) return
    resetSession()
    setMode(next)
  }

  const handleSend = async (content) => {
    const attempt = attemptRef.current
    start()
    const newMessages = [...messages, { role: 'user', content }]
    setMessages(newMessages)
    setSending(true)
    try {
      const res = await postChat(problem.id, newMessages)
      if (attempt !== attemptRef.current) return
      setMessages([...newMessages, { role: 'assistant', content: res.reply }])
      setCode(res.code)
      setLastAttemptId(res.attempt_id)
      addUsage(res.input_tokens, res.output_tokens)
    } catch (e) {
      if (attempt !== attemptRef.current) return
      setError(e.message)
    } finally {
      if (attempt === attemptRef.current) setSending(false)
    }
  }

  const handleSubmit = async () => {
    const attempt = attemptRef.current
    setSubmitting(true)
    setSubmitError(null)
    try {
      const res = await postSubmit({
        problemId: problem.id,
        code,
        inputTokens,
        outputTokens,
        elapsedSeconds: currentElapsedSeconds(),
        attemptId: mode === 'manual' ? null : lastAttemptId,
        mode,
      })
      if (attempt !== attemptRef.current) return
      setTestResults(res.test_results)
      setPassed(res.passed)
      if (res.passed) {
        stopTimer()
        const reviewRes = await postReview(problem.id, code)
        if (attempt !== attemptRef.current) return
        setReviewComments(reviewRes)
        refreshLeaderboard()
      }
    } catch (e) {
      if (attempt !== attemptRef.current) return
      setSubmitError(e.message)
    } finally {
      if (attempt === attemptRef.current) setSubmitting(false)
    }
  }

  if (error) return <p className="error">{error}</p>
  if (!problem) return <p>Loading...</p>

  const isManual = mode === 'manual'

  return (
    <div
      className={`workspace-page${resizingSidebar ? ' resizing' : ''}`}
      style={{ gridTemplateColumns: `${sidebarWidth}px 24px 1fr` }}
    >
      <div className="workspace-sidebar">
        <ModeToggle value={mode} onChange={handleModeChange} />

        <div className="workspace-description">
          <div className="workspace-title-row">
            <h1>{problem.title}</h1>
            <button className="btn btn-outline" onClick={handleReplay}>
              Replay Problem
            </button>
          </div>
          <span className={`tag tag-${problem.difficulty}`}>{problem.difficulty}</span>
          <ProblemDescription text={problem.description} />
          <pre>{problem.function_signature}</pre>
        </div>

        <div className="workspace-leaderboard">
          <h2>Leaderboard</h2>
          {leaderboardError && <p className="error">{leaderboardError}</p>}
          {!leaderboard && !leaderboardError && <p>Loading...</p>}
          {leaderboard && (leaderboard.length ? <LeaderboardTable rows={leaderboard} mode="prompt" /> : <p>No submissions yet.</p>)}
          <Link className="leaderboard-more" to={`/problems/${problemId}/leaderboard`}>
            Full leaderboard &rarr;
          </Link>
        </div>
      </div>

      <div
        className="workspace-resize-handle"
        onMouseDown={handleResizeStart}
        role="separator"
        aria-orientation="vertical"
        aria-label="Resize problem panel"
        title="Drag to resize"
      >
        <span className="workspace-resize-grip">↔</span>
      </div>

      <div className="workspace-main">
        <div className="workspace-stats">
          {!isManual && (
            <TokenCounter inputTokens={inputTokens} outputTokens={outputTokens} parTokens={problem.par_tokens} />
          )}
          <Timer elapsedSeconds={elapsedSeconds} />
        </div>

        {!isManual && (
          <ChatPanel messages={messages} onSend={handleSend} sending={sending} resetSignal={attemptRef.current} />
        )}
        <CodePanel code={code} onChange={setCode} />

        <button className="btn btn-accent" onClick={handleSubmit} disabled={submitting || sending || passed}>
          {submitting ? 'Running...' : 'Submit'}
        </button>
        {submitError && <p className="error">{submitError}</p>}

        <div ref={reviewRef}>
          <ReviewComments review={reviewComments} />
        </div>

        {testResults && (
          <div className="workspace-results">
            <h2>{passed ? 'All tests passed' : 'Some tests failed'}</h2>
            <TestResultsList results={testResults} />
          </div>
        )}
      </div>
    </div>
  )
}

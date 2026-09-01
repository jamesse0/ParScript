import { useEffect, useRef, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getProblem } from '../api/problems'
import { postChat } from '../api/chat'
import { postSubmit } from '../api/submit'
import { postReview } from '../api/review'
import { getLeaderboard, getSubmissionPrompts } from '../api/leaderboard'
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
import PromptTrace from '../components/PromptTrace'
import { difficultyLabel } from '../lib/difficulty'

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

export default function ProblemWorkspacePage({ courseContext = null }) {
  const routeParams = useParams()
  // In a course the step's problem id + a namespaced storage key come from the
  // runner; standalone it's the route param and the bare problem id.
  const problemId = courseContext ? String(courseContext.problemId) : routeParams.problemId
  const storageId = courseContext
    ? `course:${courseContext.course.slug}:${courseContext.stepIndex}`
    : problemId
  const [problem, setProblem] = useState(null)
  const [error, setError] = useState(null)

  const [saved] = useState(() => loadWorkspaceState(storageId))

  // A course step starts fresh from the carried-forward code. A saved snapshot
  // only counts as a real resume if it has chat history for this step -- an
  // untouched step's auto-save, or a stale one left by an earlier run of the
  // same course, must not shadow carryCode.
  const courseFresh = Boolean(courseContext) && !saved?.messages?.length
  const restore = courseFresh ? null : saved

  // 'prompt' = chat with the AI; 'manual' = hand-write the solution, ranked by time.
  // Course steps are always prompt mode (the whole point is measuring tokens).
  const [modeState, setModeState] = useState(restore?.mode ?? 'prompt')
  const mode = courseContext ? 'prompt' : modeState

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

  const [messages, setMessages] = useState(restore?.messages ?? [])
  const [code, setCode] = useState(
    courseFresh ? (courseContext.carryCode ?? '') : (saved?.code ?? ''),
  )
  const [lastAttemptId, setLastAttemptId] = useState(restore?.lastAttemptId ?? null)
  const [submissionId, setSubmissionId] = useState(restore?.submissionId ?? null)
  const [sending, setSending] = useState(false)

  const [submitting, setSubmitting] = useState(false)
  const [testResults, setTestResults] = useState(restore?.testResults ?? null)
  const [passed, setPassed] = useState(restore?.passed ?? false)
  const [reviewComments, setReviewComments] = useState(restore?.reviewComments ?? null)
  const [submitError, setSubmitError] = useState(null)

  const [leaderboard, setLeaderboard] = useState(null)
  const [leaderboardError, setLeaderboardError] = useState(null)
  const [trace, setTrace] = useState(null) // { open, loading, error, data }

  const attemptRef = useRef(0)
  const reviewRef = useRef(null)

  const { inputTokens, outputTokens, reasoningTokens, addUsage, reset: resetTokens } = useTokenCounter(
    restore?.inputTokens,
    restore?.outputTokens,
    restore?.reasoningTokens,
  )
  const {
    elapsedSeconds,
    start: startTimer,
    pause: pauseTimer,
    stop: stopTimer,
    currentElapsedSeconds,
    reset: resetTimer,
  } = useElapsedTimer(restore?.elapsedSeconds)

  useEffect(() => {
    getProblem(problemId)
      .then((p) => {
        setProblem(p)
        if (courseFresh || restore?.code === undefined) {
          // Course step N>0 pre-fills with the code submitted for step N-1.
          setCode(courseContext?.carryCode ?? p.starter_code)
        }
      })
      .catch((e) => setError(e.message))
  }, [problemId, saved])

  // Manual mode: the clock runs continuously from the moment the page is ready.
  // (Prompt mode instead resumes/pauses the timer around each LLM call in
  // handleSend, so it only counts time spent waiting on the model.)
  useEffect(() => {
    if (problem && mode === 'manual' && !passed) startTimer()
  }, [problem, mode, passed, startTimer])

  useEffect(() => {
    saveWorkspaceState(storageId, {
      mode,
      messages,
      code,
      lastAttemptId,
      submissionId,
      testResults,
      passed,
      reviewComments,
      inputTokens,
      outputTokens,
      reasoningTokens,
      elapsedSeconds,
    })
  }, [
    storageId,
    mode,
    messages,
    code,
    lastAttemptId,
    submissionId,
    testResults,
    passed,
    reviewComments,
    inputTokens,
    outputTokens,
    reasoningTokens,
    elapsedSeconds,
  ])

  const refreshLeaderboard = () => {
    // Course runner shows a course-progress panel instead of the per-problem board.
    if (courseContext) return
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

  const openTrace = async (row) => {
    setTrace({ open: true, loading: true, error: null, data: null })
    try {
      const data = await getSubmissionPrompts(row.submission_id)
      setTrace({ open: true, loading: false, error: null, data })
    } catch (e) {
      const msg =
        e.status === 403
          ? "Submit a working solution to this problem to see other players' prompts."
          : e.message
      setTrace({ open: true, loading: false, error: msg, data: null })
    }
  }

  useEffect(() => {
    if (reviewComments) {
      reviewRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    }
  }, [reviewComments])

  const resetSession = () => {
    attemptRef.current += 1
    clearWorkspaceState(storageId)
    setMessages([])
    setCode(courseContext?.carryCode ?? problem.starter_code)
    setLastAttemptId(null)
    setSubmissionId(null)
    setSending(false)
    setSubmitting(false)
    setTestResults(null)
    setPassed(false)
    setReviewComments(null)
    setSubmitError(null)
    resetTokens()
    resetTimer()
  }

  const handleReset = () => {
    resetSession()
  }

  const handleModeChange = (next) => {
    if (next === mode) return
    resetSession()
    setModeState(next)
  }

  const handleSend = async (content) => {
    const attempt = attemptRef.current
    // Prompt-mode timer: runs only while a generation is in flight. Resume on
    // send, pause once the response (or an error) comes back -- see finally.
    startTimer()
    // First turn of a course step: hand the model the code carried over from the
    // previous step as context. This synthetic exchange is sent to the API only --
    // it is NOT shown in the chat transcript.
    const carryPrefix =
      courseContext && messages.length === 0
        ? [
            {
              role: 'user',
              content:
                'Here is the code carried over from the previous step. Build on it:\n```python\n' +
                code +
                '\n```',
            },
            {
              role: 'assistant',
              content: "Understood — I'll extend this code.\n```python\n" + code + '\n```',
            },
          ]
        : []
    const visibleMessages = [...messages, { role: 'user', content }]
    const outgoing = [...messages, ...carryPrefix, { role: 'user', content }]
    setMessages(visibleMessages)
    setSending(true)
    try {
      const res = await postChat(problem.id, outgoing)
      if (attempt !== attemptRef.current) return
      setMessages([
        ...visibleMessages,
        {
          role: 'assistant',
          content: res.reply,
          reasoningSummary: res.reasoning_summary,
          reasoningTokens: res.reasoning_tokens,
        },
      ])
      setCode(res.code)
      setLastAttemptId(res.attempt_id)
      addUsage(res.input_tokens, res.output_tokens, res.reasoning_tokens)
    } catch (e) {
      if (attempt !== attemptRef.current) return
      setError(e.message)
    } finally {
      if (attempt === attemptRef.current) {
        pauseTimer()
        setSending(false)
      }
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
      setSubmissionId(res.submission_id)
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

  const handleCourseNext = () => {
    courseContext.onStepComplete({
      code,
      submissionId,
      inputTokens,
      outputTokens,
      elapsedSeconds: currentElapsedSeconds(),
    })
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
        {!courseContext && <ModeToggle value={mode} onChange={handleModeChange} />}

        <div className="workspace-description">
          <div className="workspace-title-row">
            <h1>{problem.title}</h1>
            <button className="btn btn-outline" onClick={handleReset}>
              {courseContext ? 'Restart step' : 'Reset Problem'}
            </button>
          </div>
          <span className={`tag tag-${problem.difficulty}`}>{difficultyLabel(problem.difficulty)}</span>
          <ProblemDescription text={problem.description} />
          <pre>{problem.function_signature}</pre>
          {problem.test_kind === 'pytest' && (
            <p className="workspace-hint">
              Graded by a hidden test suite. Match the exact class and method names in the
              signature above &mdash; a mismatch fails every test.
            </p>
          )}
        </div>

        {courseContext ? (
          <div className="workspace-course-progress">
            <h2>{courseContext.course.title}</h2>
            <p className="course-step-indicator">
              Step {courseContext.stepIndex + 1} / {courseContext.totalSteps}
            </p>
            <ol className="course-step-list">
              {courseContext.course.steps.map((s, i) => (
                <li
                  key={s.problem_id}
                  className={
                    i < courseContext.stepIndex
                      ? 'done'
                      : i === courseContext.stepIndex
                        ? 'current'
                        : undefined
                  }
                >
                  {s.title}
                </li>
              ))}
            </ol>
            <p className="course-running-total">
              {(courseContext.priorTokens + inputTokens + outputTokens).toLocaleString()} tokens so far
            </p>
          </div>
        ) : (
          <div className="workspace-leaderboard">
            <h2>Leaderboard</h2>
            {leaderboardError && <p className="error">{leaderboardError}</p>}
            {!leaderboard && !leaderboardError && <p>Loading...</p>}
            {leaderboard &&
              (leaderboard.length ? (
                <LeaderboardTable rows={leaderboard.slice(0, 3)} mode="prompt" onSelectRow={openTrace} />
              ) : (
                <p>No submissions yet.</p>
              ))}
            <Link className="leaderboard-more" to={`/problems/${problemId}/leaderboard`}>
              Full leaderboard &rarr;
            </Link>
          </div>
        )}
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
            <TokenCounter
              inputTokens={inputTokens}
              outputTokens={outputTokens}
              reasoningTokens={reasoningTokens}
              parTokens={problem.par_tokens}
            />
          )}
          <Timer elapsedSeconds={elapsedSeconds} />
        </div>

        {!isManual && (
          <ChatPanel messages={messages} onSend={handleSend} sending={sending} resetSignal={attemptRef.current} />
        )}
        <CodePanel code={code} onChange={setCode} readOnly={!isManual} />

        <button className="btn btn-accent" onClick={handleSubmit} disabled={submitting || sending || passed}>
          {submitting ? 'Running...' : 'Submit'}
        </button>
        {submitError && <p className="error">{submitError}</p>}

        {courseContext && passed && (
          <button className="btn btn-accent workspace-course-next" onClick={handleCourseNext}>
            {courseContext.stepIndex + 1 < courseContext.totalSteps
              ? 'Next step →'
              : 'Finish course →'}
          </button>
        )}

        <div ref={reviewRef}>
          <ReviewComments review={reviewComments} />
        </div>

        {testResults && (
          <div className="workspace-results">
            <h2>{passed ? 'All tests passed' : 'Some tests failed'}</h2>
            <TestResultsList results={testResults} testKind={problem.test_kind} />
          </div>
        )}
      </div>

      <PromptTrace
        open={Boolean(trace?.open)}
        loading={Boolean(trace?.loading)}
        error={trace?.error}
        data={trace?.data}
        onClose={() => setTrace(null)}
      />
    </div>
  )
}

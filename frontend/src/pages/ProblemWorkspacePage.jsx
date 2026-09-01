import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
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
import Markdown from '../components/Markdown'

export default function ProblemWorkspacePage() {
  const { problemId } = useParams()
  const [problem, setProblem] = useState(null)
  const [error, setError] = useState(null)

  const [saved] = useState(() => loadWorkspaceState(problemId))

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

  useEffect(() => {
    saveWorkspaceState(problemId, {
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
    getLeaderboard(problemId)
      .then((rows) => {
        setLeaderboard(rows)
        setLeaderboardError(null)
      })
      .catch((e) => setLeaderboardError(e.message))
  }

  useEffect(() => {
    refreshLeaderboard()
  }, [problemId])

  const handleSend = async (content) => {
    start()
    const newMessages = [...messages, { role: 'user', content }]
    setMessages(newMessages)
    setSending(true)
    try {
      const res = await postChat(problem.id, newMessages)
      setMessages([...newMessages, { role: 'assistant', content: res.reply }])
      setCode(res.code)
      setLastAttemptId(res.attempt_id)
      addUsage(res.input_tokens, res.output_tokens)
    } catch (e) {
      setError(e.message)
    } finally {
      setSending(false)
    }
  }

  const handleSubmit = async () => {
    setSubmitting(true)
    setSubmitError(null)
    try {
      const res = await postSubmit({
        problemId: problem.id,
        code,
        inputTokens,
        outputTokens,
        elapsedSeconds: currentElapsedSeconds(),
        attemptId: lastAttemptId,
      })
      setTestResults(res.test_results)
      setPassed(res.passed)
      if (res.passed) {
        stopTimer()
        const reviewRes = await postReview(problem.id, code)
        setReviewComments(reviewRes)
        refreshLeaderboard()
      }
    } catch (e) {
      setSubmitError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  const handleReplay = () => {
    clearWorkspaceState(problemId)
    setMessages([])
    setCode(problem.starter_code)
    setLastAttemptId(null)
    setTestResults(null)
    setPassed(false)
    setReviewComments(null)
    setSubmitError(null)
    resetTokens()
    resetTimer()
  }

  if (error) return <p className="error">{error}</p>
  if (!problem) return <p>Loading...</p>

  return (
    <div className="workspace-page">
      <div className="workspace-sidebar">
        <div className="workspace-description">
          <h1>{problem.title}</h1>
          <span className={`tag tag-${problem.difficulty}`}>{problem.difficulty}</span>
          <Markdown text={problem.description} />
          <pre>{problem.function_signature}</pre>
        </div>

        <div className="workspace-leaderboard">
          <h2>Leaderboard</h2>
          {leaderboardError && <p className="error">{leaderboardError}</p>}
          {!leaderboard && !leaderboardError && <p>Loading...</p>}
          {leaderboard && (leaderboard.length ? <LeaderboardTable rows={leaderboard} /> : <p>No submissions yet.</p>)}
        </div>
      </div>

      <div className="workspace-main">
        <div className="workspace-stats">
          <TokenCounter inputTokens={inputTokens} outputTokens={outputTokens} parTokens={problem.par_tokens} />
          <Timer elapsedSeconds={elapsedSeconds} />
        </div>

        <ChatPanel messages={messages} onSend={handleSend} sending={sending} />
        <CodePanel code={code} />

        <button className="btn btn-accent" onClick={handleSubmit} disabled={submitting}>
          {submitting ? 'Running...' : 'Submit'}
        </button>
        {submitError && <p className="error">{submitError}</p>}

        {testResults && (
          <div className="workspace-results">
            <h2>{passed ? 'All tests passed' : 'Some tests failed'}</h2>
            <TestResultsList results={testResults} />
            <button className="btn btn-outline" onClick={handleReplay}>Replay Problem</button>
          </div>
        )}

        <ReviewComments review={reviewComments} />
      </div>
    </div>
  )
}

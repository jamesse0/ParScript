import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getProblem } from '../api/problems'
import { postChat } from '../api/chat'
import { postSubmit } from '../api/submit'
import { postReview } from '../api/review'
import { useTokenCounter } from '../hooks/useTokenCounter'
import { useElapsedTimer } from '../hooks/useElapsedTimer'
import ChatPanel from '../components/ChatPanel'
import CodePanel from '../components/CodePanel'
import TokenCounter from '../components/TokenCounter'
import Timer from '../components/Timer'
import TestResultsList from '../components/TestResultsList'
import ReviewComments from '../components/ReviewComments'

export default function ProblemWorkspacePage() {
  const { problemId } = useParams()
  const [problem, setProblem] = useState(null)
  const [error, setError] = useState(null)

  const [messages, setMessages] = useState([])
  const [code, setCode] = useState('')
  const [lastAttemptId, setLastAttemptId] = useState(null)
  const [codeDirty, setCodeDirty] = useState(false)
  const [sending, setSending] = useState(false)

  const [submitting, setSubmitting] = useState(false)
  const [testResults, setTestResults] = useState(null)
  const [passed, setPassed] = useState(false)
  const [reviewComments, setReviewComments] = useState(null)
  const [submitError, setSubmitError] = useState(null)

  const { inputTokens, outputTokens, addUsage } = useTokenCounter()
  const { elapsedSeconds, start, currentElapsedSeconds } = useElapsedTimer()

  useEffect(() => {
    getProblem(problemId)
      .then((p) => {
        setProblem(p)
        setCode(p.starter_code)
      })
      .catch((e) => setError(e.message))
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
      setCodeDirty(false)
      setLastAttemptId(res.attempt_id)
      addUsage(res.input_tokens, res.output_tokens)
    } catch (e) {
      setError(e.message)
    } finally {
      setSending(false)
    }
  }

  const handleCodeChange = (value) => {
    setCode(value)
    setCodeDirty(true)
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
        attemptId: codeDirty ? null : lastAttemptId,
      })
      setTestResults(res.test_results)
      setPassed(res.passed)
      if (res.passed) {
        const reviewRes = await postReview(problem.id, code)
        setReviewComments(reviewRes.comments)
      }
    } catch (e) {
      setSubmitError(e.message)
    } finally {
      setSubmitting(false)
    }
  }

  if (error) return <p className="error">{error}</p>
  if (!problem) return <p>Loading...</p>

  return (
    <div className="workspace-page">
      <div className="workspace-description">
        <h1>{problem.title}</h1>
        <span className={`tag tag-${problem.difficulty}`}>{problem.difficulty}</span>
        <p>{problem.description}</p>
        <pre>{problem.function_signature}</pre>
      </div>

      <div className="workspace-main">
        <div className="workspace-stats">
          <TokenCounter inputTokens={inputTokens} outputTokens={outputTokens} parTokens={problem.par_tokens} />
          <Timer elapsedSeconds={elapsedSeconds} />
        </div>

        <ChatPanel messages={messages} onSend={handleSend} sending={sending} />
        <CodePanel code={code} onChange={handleCodeChange} />

        <button className="btn btn-accent" onClick={handleSubmit} disabled={submitting}>
          {submitting ? 'Running...' : 'Submit'}
        </button>
        {submitError && <p className="error">{submitError}</p>}

        {testResults && (
          <div className="workspace-results">
            <h2>{passed ? 'All tests passed' : 'Some tests failed'}</h2>
            <TestResultsList results={testResults} />
          </div>
        )}

        <ReviewComments comments={reviewComments} />
      </div>
    </div>
  )
}

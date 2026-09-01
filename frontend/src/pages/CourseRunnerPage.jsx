import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { getCourse, completeCourse } from '../api/courses'
import { loadCourseState, saveCourseState, clearCourseState } from '../lib/courseStorage'
import { clearWorkspaceState } from '../lib/workspaceStorage'
import ProblemWorkspacePage from './ProblemWorkspacePage'
import CourseScore from './CourseScore'

// Controller for a course run. Renders one ProblemWorkspacePage per step; the
// `key` forces a clean remount each step so every per-step hook resets. The code
// submitted for step N becomes step N+1's starter code (carryCode).
export default function CourseRunnerPage() {
  const { courseSlug } = useParams()
  const [course, setCourse] = useState(null)
  const [error, setError] = useState(null)
  const [progress, setProgress] = useState(() => loadCourseState(courseSlug))
  const [completion, setCompletion] = useState(null) // { res, steps } once the last step is done
  const [finishing, setFinishing] = useState(false)

  useEffect(() => {
    getCourse(courseSlug)
      .then(setCourse)
      .catch((e) => setError(e.message))
  }, [courseSlug])

  const steps = course?.steps ?? []
  const stepIndex = progress?.stepIndex ?? 0
  const doneSteps = progress?.steps ?? []
  const priorTokens = doneSteps.reduce((n, s) => n + s.inputTokens + s.outputTokens, 0)
  const allDone = steps.length > 0 && doneSteps.length >= steps.length

  const runCompletion = async (done) => {
    setFinishing(true)
    try {
      const res = await completeCourse(
        courseSlug,
        done.map((s) => s.submissionId),
      )
      setCompletion({ res, steps: done })
    } catch (e) {
      setError(e.message)
    } finally {
      setFinishing(false)
    }
  }

  // Resume: reloaded after finishing the last step but before the score posted.
  useEffect(() => {
    if (allDone && !completion && !finishing) runCompletion(doneSteps)
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [allDone])

  const onStepComplete = ({ code, submissionId, inputTokens, outputTokens, elapsedSeconds }) => {
    // Guard against a double click / reload replay: this step is already recorded.
    if (doneSteps.length !== stepIndex) return
    const nextDone = [...doneSteps, { submissionId, inputTokens, outputTokens, elapsedSeconds }]
    const isLast = stepIndex + 1 >= steps.length
    if (!isLast) {
      // The next step must start from this step's code, not a stale workspace
      // snapshot left by an earlier run of the course.
      clearWorkspaceState(`course:${courseSlug}:${stepIndex + 1}`)
    }
    const next = {
      stepIndex: isLast ? stepIndex : stepIndex + 1,
      carryCode: code,
      steps: nextDone,
    }
    setProgress(next)
    saveCourseState(courseSlug, next)
    if (isLast) runCompletion(nextDone)
  }

  const handleRestartCourse = () => {
    steps.forEach((_, i) => clearWorkspaceState(`course:${courseSlug}:${i}`))
    clearCourseState(courseSlug)
    setProgress(null)
    setCompletion(null)
    setError(null)
  }

  const confirmRestartCourse = () => {
    if (
      window.confirm(
        'Restart this course from step 1? Your in-progress code and chat for every step will be cleared.',
      )
    ) {
      handleRestartCourse()
    }
  }

  if (error) return <p className="error">{error}</p>
  if (!course) return <p>Loading...</p>

  if (completion) {
    return (
      <CourseScore
        course={course}
        completion={completion.res}
        steps={completion.steps}
        onRestart={handleRestartCourse}
      />
    )
  }

  const current = steps[stepIndex]
  if (!current) return <p>Loading...</p>

  return (
    <div className="course-runner">
      <div className="course-runner-bar">
        <span className="course-runner-title">{course.title}</span>
        <span className="course-runner-progress">
          Step {stepIndex + 1} / {steps.length} · {priorTokens.toLocaleString()} tokens so far
        </span>
        {finishing && <span className="course-runner-finishing">Scoring…</span>}
        <button
          className="btn btn-outline course-runner-restart"
          onClick={confirmRestartCourse}
          disabled={finishing}
        >
          Restart course
        </button>
      </div>
      <ProblemWorkspacePage
        key={`${courseSlug}:${stepIndex}`}
        courseContext={{
          course,
          stepIndex,
          totalSteps: steps.length,
          problemId: current.problem_id,
          carryCode: stepIndex === 0 ? undefined : progress?.carryCode,
          priorTokens,
          onStepComplete,
        }}
      />
    </div>
  )
}

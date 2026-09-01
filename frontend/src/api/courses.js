import { api } from '../lib/api'

// -> CourseSummary[]: { slug, title, description, step_count, par_tokens }
export const getCourses = () => api('/courses')

// -> CourseDetail: { slug, title, description, step_count, par_tokens,
//                    steps: [{ position, problem_id, title, par_tokens }] }
export const getCourse = (slug) => api(`/courses/${slug}`)

// submissionIds: the winning (passing) submission id for each step, in order.
// -> { total_input_tokens, total_output_tokens, elapsed_seconds, par_tokens, completed_at }
export const completeCourse = (slug, submissionIds) =>
  api(`/courses/${slug}/complete`, {
    method: 'POST',
    body: JSON.stringify({ submission_ids: submissionIds }),
  })

// -> CourseLeaderboardRow[]: { username, user_id, total_input_tokens,
//                              total_output_tokens, elapsed_seconds, completed_at }
export const getCourseLeaderboard = (slug) => api(`/courses/${slug}/leaderboard`)

import { supabase } from './supabase'

// Every backend request/response that carries a problem id must send it as a
// string in JSON bodies even though it comes back as a number from GET
// endpoints — see CLAUDE.md "Known issues" (SubmitRequest/ChatRequest/
// ReviewRequest.problem_id is typed str; ProblemSummary.id is typed int).
export const asProblemId = (id) => String(id)

export async function api(path, options = {}) {
  const { data } = await supabase.auth.getSession()
  const token = data.session?.access_token

  const res = await fetch(`${import.meta.env.VITE_API_BASE_URL}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  })
  if (!res.ok) throw Object.assign(new Error(`${res.status} ${path}`), { status: res.status, res })
  return res.status === 204 ? null : res.json()
}

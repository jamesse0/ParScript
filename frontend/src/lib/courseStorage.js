const STORAGE_PREFIX = 'parscript:course:'

// Progress through a course sequence, so a reload resumes at the right step with
// the carried-forward code intact. Per-step workspace state (chat/code/timer)
// still lives in workspaceStorage under a namespaced id: course:<slug>:<index>.
//   { stepIndex, carryCode, steps: [{ submissionId, inputTokens, outputTokens, elapsedSeconds }] }
export function loadCourseState(slug) {
  try {
    const raw = localStorage.getItem(STORAGE_PREFIX + slug)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function saveCourseState(slug, state) {
  try {
    localStorage.setItem(STORAGE_PREFIX + slug, JSON.stringify(state))
  } catch {
    // storage full or disabled -- not worth surfacing to the user
  }
}

export function clearCourseState(slug) {
  try {
    localStorage.removeItem(STORAGE_PREFIX + slug)
  } catch {
    // ignore
  }
}

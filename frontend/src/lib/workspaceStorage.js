const STORAGE_PREFIX = 'parscript:workspace:'

// Persists in-progress chat/code/timer state per problem so a page reload
// doesn't wipe it (DESIGN.md lists this as a stretch cut, picking it up now
// that the MVP works end-to-end).
export function loadWorkspaceState(problemId) {
  try {
    const raw = localStorage.getItem(STORAGE_PREFIX + problemId)
    return raw ? JSON.parse(raw) : null
  } catch {
    return null
  }
}

export function saveWorkspaceState(problemId, state) {
  try {
    localStorage.setItem(STORAGE_PREFIX + problemId, JSON.stringify(state))
  } catch {
    // storage full or disabled — not worth surfacing to the user
  }
}

export function clearWorkspaceState(problemId) {
  try {
    localStorage.removeItem(STORAGE_PREFIX + problemId)
  } catch {
    // ignore
  }
}

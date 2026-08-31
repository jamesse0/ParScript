import { api } from '../lib/api'

// -> MeResponse { id, username, created_at }, or throws with status 404 if not onboarded yet
export const getMe = () => api('/me')

// -> MeResponse; throws with status 409 (taken/exists) or 422 (invalid) on failure
export const createProfile = (username) =>
  api('/me/profile', { method: 'POST', body: JSON.stringify({ username }) })

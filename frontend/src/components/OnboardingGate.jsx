import { useEffect, useState } from 'react'
import { useAuth } from '../lib/AuthProvider'
import { getMe, createProfile } from '../api/profile'
import UsernamePrompt from './UsernamePrompt'

// Wraps authed routes: a Supabase login alone doesn't create a `profiles` row,
// so gate on GET /me and show the username prompt on a 404 (see AUTH.md §7).
export default function OnboardingGate({ children }) {
  const { session } = useAuth()
  const [profile, setProfile] = useState(undefined) // undefined = loading

  useEffect(() => {
    if (!session) return
    getMe()
      .then(setProfile)
      .catch((e) => {
        if (e.status === 404) setProfile(null)
        else throw e
      })
  }, [session])

  if (profile === undefined) return <p>Loading...</p>
  if (profile === null) {
    return <UsernamePrompt onSubmit={async (username) => setProfile(await createProfile(username))} />
  }
  return children
}

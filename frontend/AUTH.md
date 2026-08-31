# Frontend auth setup (Supabase + GitHub OAuth)

How the React/Vite frontend logs a user in and talks to the FastAPI backend.
The backend side (`deps.get_current_user`, `GET /me`, `POST /me/profile`) is already
built; this doc is the frontend half. Dashboard / GitHub setup lives in
[../supabase/README.md](../supabase/README.md) §2 — do that first.

## Flow

```
[Login button] --signInWithOAuth('github')--> GitHub --> Supabase /auth/v1/callback
     |                                                          |
     |<-------- redirect back to app with a session ------------|
     |          (supabase-js reads it from the URL itself)
     |
 getSession() -> access_token (JWT)
     |
 GET /me  (Authorization: Bearer <access_token>)
     |-- 200 --> has profile, go to app
     |-- 404 --> show username prompt --> POST /me/profile {username} --> 201
```

The callback URL is Supabase's, not ours. GitHub → Supabase → back to us. `supabase-js`
auto-detects the returned session on page load (`detectSessionInUrl`, on by default), so
there is nothing to parse by hand.

## 1. Install

```sh
npm install @supabase/supabase-js
```

## 2. Environment variables

`frontend/.env` (Vite only exposes vars prefixed `VITE_`):

```
VITE_SUPABASE_URL=https://geajcmgmnedqcvqbmnjl.supabase.co
VITE_SUPABASE_ANON_KEY=<the anon / publishable key from Supabase → Settings → API>
VITE_API_BASE_URL=http://localhost:8000
```

**Never** put `SUPABASE_SERVICE_KEY` or `SUPABASE_JWT_SECRET` here. The anon key is meant
to be public — RLS protects the data, and all real writes go through the backend anyway.
Add `frontend/.env` to `.gitignore`; commit a `frontend/.env.example` with blank values.

## 3. The Supabase client (one instance, shared)

```js
// src/lib/supabase.js
import { createClient } from '@supabase/supabase-js'

export const supabase = createClient(
  import.meta.env.VITE_SUPABASE_URL,
  import.meta.env.VITE_SUPABASE_ANON_KEY,
)
```

Defaults are fine: it persists the session to `localStorage` and auto-refreshes the
access token before it expires.

## 4. Auth context

Track the session once at the app root and expose it via context.

```jsx
// src/lib/AuthProvider.jsx
import { createContext, useContext, useEffect, useState } from 'react'
import { supabase } from './supabase'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    supabase.auth.getSession().then(({ data }) => {
      setSession(data.session)
      setLoading(false)
    })
    const { data: sub } = supabase.auth.onAuthStateChange((_event, s) => setSession(s))
    return () => sub.subscription.unsubscribe()
  }, [])

  return (
    <AuthContext.Provider value={{ session, loading }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)
```

Wrap `<App/>` in `<AuthProvider>` in `main.jsx`.

## 5. Sign in / sign out

```jsx
import { supabase } from '../lib/supabase'

export function LoginButton() {
  const signIn = () =>
    supabase.auth.signInWithOAuth({
      provider: 'github',
      options: { redirectTo: window.location.origin },
    })
  return <button onClick={signIn}>Continue with GitHub</button>
}

export const signOut = () => supabase.auth.signOut()
```

`redirectTo` must be listed in Supabase → Authentication → URL Configuration → Redirect URLs.
For local dev that's `http://localhost:5173/**`.

## 6. Calling the backend

Always pull a fresh token from `getSession()` (it may have been refreshed) and send it as
a Bearer header.

```js
// src/lib/api.js
import { supabase } from './supabase'

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
```

Public endpoints (`GET /problems`, `GET /problems/{id}`, `GET /leaderboard/{id}`) work with
no token. Authed endpoints (`GET /me`, `POST /me/profile`, `GET /me/metrics`, `POST /chat`,
`POST /submit`, `POST /review`) need the header.

## 7. Onboarding gate

A Supabase login does **not** create a `profiles` row — the user picks a username first.

```jsx
// after session is present, before showing the main app
const [profile, setProfile] = useState(undefined) // undefined = loading

useEffect(() => {
  if (!session) return
  api('/me')
    .then(setProfile)                                  // 200 -> has profile
    .catch((e) => { if (e.status === 404) setProfile(null); else throw e })
}, [session])

// profile === null  -> render <UsernamePrompt/>
// profile           -> render the app

async function submitUsername(username) {
  try {
    setProfile(await api('/me/profile', { method: 'POST', body: JSON.stringify({ username }) }))
  } catch (e) {
    if (e.status === 409) showError('That username is taken')
    else if (e.status === 422) showError('3–30 chars: letters, digits, underscores')
    else throw e
  }
}
```

## 8. Protecting routes

```jsx
function RequireAuth({ children }) {
  const { session, loading } = useAuth()
  if (loading) return <Spinner />
  if (!session) return <Navigate to="/login" replace />
  return children
}
```

Wrap the workspace / metrics routes in `<RequireAuth>`. The leaderboard and problem list can
stay public.

## Local dev checklist

- [ ] GitHub OAuth App created, callback = `https://geajcmgmnedqcvqbmnjl.supabase.co/auth/v1/callback`
- [ ] Supabase → Providers → GitHub enabled with Client ID + Secret
- [ ] Supabase → URL Configuration: Site URL `http://localhost:5173`, redirect `http://localhost:5173/**`
- [ ] `frontend/.env` has `VITE_SUPABASE_URL`, `VITE_SUPABASE_ANON_KEY`, `VITE_API_BASE_URL`
- [ ] Backend running (`uvicorn main:app --reload`) with `CORS_ORIGINS` including `http://localhost:5173` (default)
- [ ] Vite dev server on port 5173 (`npm run dev`)

## Gotchas

- **Redirect loop / "requested path is invalid":** the `redirectTo` origin isn't in the
  Supabase redirect allowlist.
- **CORS error calling the backend:** `CORS_ORIGINS` in `backend/.env` doesn't include the
  exact frontend origin (scheme + host + port).
- **401 from the backend right after login:** you sent a stale token — call `getSession()`
  per request (as in `api.js`) instead of caching `access_token` in a variable.
- **Session lost on refresh:** don't disable `persistSession`; don't create the client more
  than once.
- **`GET /me` 404 is not an error** — it's the signal to show the username prompt.

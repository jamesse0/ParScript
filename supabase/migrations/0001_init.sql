-- ParScript initial schema.
--
-- Model (differs from DESIGN.md §4-5 on purpose, so a run is fully reproducible):
--   attempts    = one row per CHAT submit  (prompt sent to the model + code it returned).
--                 Never updated. No test results here.
--   submissions = one row per RUN-TESTS submit (exact code executed + per-test results).
--                 Every run, pass or fail. Never updated.
--   "first pass" / leaderboard = DERIVED: earliest passed submission per (user, problem).
--
-- The FastAPI backend connects with the Supabase service-role key, which bypasses RLS.
-- RLS is still enabled on every table so the anon/auth key can't read or write directly.

-- ---------------------------------------------------------------------------
-- profiles
-- ---------------------------------------------------------------------------
create table if not exists public.profiles (
    id         uuid primary key references auth.users (id) on delete cascade,
    username   text unique not null,
    created_at timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- problems
-- ---------------------------------------------------------------------------
create table if not exists public.problems (
    id                 bigint generated always as identity primary key,
    slug               text unique not null,
    title              text not null,
    description        text not null,
    difficulty         text not null check (difficulty in ('easy', 'medium', 'hard')),
    par_tokens         integer not null,
    function_signature text not null,
    starter_code       text not null,
    -- array of {input, expected_output}
    test_cases         jsonb not null,
    created_at         timestamptz not null default now()
);

-- ---------------------------------------------------------------------------
-- attempts  (chat submissions -- never updated)
-- ---------------------------------------------------------------------------
create table if not exists public.attempts (
    id              uuid primary key default gen_random_uuid(),
    user_id         uuid not null references public.profiles (id) on delete cascade,
    problem_id      bigint not null references public.problems (id),
    -- full [{role, content}, ...] sent to the model, including this turn's user message
    message_history jsonb not null,
    reply           text,          -- assistant's text reply
    code            text,          -- code parsed out of this reply (nullable)
    input_tokens    integer not null default 0,
    output_tokens   integer not null default 0,
    model           text,          -- optional; helps replay the exact call
    created_at      timestamptz not null default now()
);

create index if not exists attempts_user_problem_idx
    on public.attempts (user_id, problem_id, created_at);

-- ---------------------------------------------------------------------------
-- submissions  (test-case runs -- never updated, one per Run-tests click)
-- ---------------------------------------------------------------------------
create table if not exists public.submissions (
    id              uuid primary key default gen_random_uuid(),
    user_id         uuid not null references public.profiles (id) on delete cascade,
    problem_id      bigint not null references public.problems (id),
    -- the chat attempt whose code was tested; null if the user hand-wrote / edited it
    attempt_id      uuid references public.attempts (id),
    code            text not null,          -- exact code executed
    -- array of {input, expected_output, actual_output, passed}
    test_results    jsonb not null,
    passed          boolean not null,
    -- client-accumulated session totals at submit time (tokens trusted client-side, DESIGN §9)
    input_tokens    integer not null default 0,
    output_tokens   integer not null default 0,
    elapsed_seconds numeric not null default 0,
    created_at      timestamptz not null default now()
);

create index if not exists submissions_problem_passed_idx
    on public.submissions (problem_id, passed, created_at);

create index if not exists submissions_user_idx
    on public.submissions (user_id, created_at);

-- ---------------------------------------------------------------------------
-- leaderboard_entries  (view: earliest passing run per user+problem)
--
-- Backend-only. This view runs with the definer's rights and is NOT RLS-aware,
-- so the frontend must never query it directly -- it goes through GET /leaderboard/{id}.
-- ---------------------------------------------------------------------------
create or replace view public.leaderboard_entries as
select distinct on (s.user_id, s.problem_id)
    s.problem_id,
    s.user_id,
    p.username,
    s.input_tokens                     as total_input_tokens,
    s.output_tokens                    as total_output_tokens,
    (s.input_tokens + s.output_tokens) as total_tokens,
    s.elapsed_seconds,
    s.created_at
from public.submissions s
join public.profiles p on p.id = s.user_id
where s.passed
order by s.user_id, s.problem_id, s.created_at asc;

-- ---------------------------------------------------------------------------
-- Row level security
-- ---------------------------------------------------------------------------
alter table public.profiles    enable row level security;
alter table public.problems    enable row level security;
alter table public.attempts    enable row level security;
alter table public.submissions enable row level security;

-- problems are public read-only reference data
drop policy if exists "problems are readable" on public.problems;
create policy "problems are readable" on public.problems
    for select using (true);

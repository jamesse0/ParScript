-- Courses: an ordered sequence of course-exclusive problems where the code you
-- submit for step N pre-fills step N+1. Scored on total tokens across the
-- sequence, with its own leaderboard. Individual step submissions stay normal
-- (they still count on each problem's own leaderboard + /me/metrics).

create table if not exists public.courses (
    id          bigint generated always as identity primary key,
    slug        text unique not null,
    title       text not null,
    description text not null,
    created_at  timestamptz not null default now()
);

create table if not exists public.course_problems (
    course_id  bigint not null references public.courses (id) on delete cascade,
    problem_id bigint not null references public.problems (id) on delete cascade,
    position   integer not null,
    primary key (course_id, problem_id),
    unique (course_id, position)
);

create index if not exists course_problems_course_pos_idx
    on public.course_problems (course_id, position);

-- one persistent score per (user, course): the best (lowest-token) completed run
create table if not exists public.course_completions (
    id                  uuid primary key default gen_random_uuid(),
    user_id             uuid not null references public.profiles (id) on delete cascade,
    course_id           bigint not null references public.courses (id) on delete cascade,
    total_input_tokens  integer not null default 0,
    total_output_tokens integer not null default 0,
    elapsed_seconds     numeric not null default 0,
    completed_at        timestamptz not null default now(),
    unique (user_id, course_id)
);

create index if not exists course_completions_course_rank_idx
    on public.course_completions (course_id, total_input_tokens, total_output_tokens);

-- hide course-exclusive problems from the normal problem list; existing rows -> false
alter table public.problems
    add column if not exists course_only boolean not null default false;

-- RLS: courses/course_problems readable by anyone (like problems);
-- course_completions has no policy -> service-role writes only (like submissions).
alter table public.courses            enable row level security;
alter table public.course_problems    enable row level security;
alter table public.course_completions enable row level security;

drop policy if exists "courses are readable" on public.courses;
create policy "courses are readable" on public.courses
    for select using (true);

drop policy if exists "course_problems are readable" on public.course_problems;
create policy "course_problems are readable" on public.course_problems
    for select using (true);

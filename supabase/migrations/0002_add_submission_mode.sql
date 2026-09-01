-- Manual mode: every submission is tagged as AI-assisted ('prompt') or
-- hand-written ('manual'). Existing rows backfill to 'prompt' via the default.
--
-- Manual submissions:
--   - are ranked on the leaderboard by time-to-solve, not tokens
--   - are excluded from GET /me/metrics entirely
--   - still run the sandbox tests and the post-pass AI review

alter table public.submissions
    add column if not exists mode text not null default 'prompt'
    check (mode in ('prompt', 'manual'));

create index if not exists submissions_problem_mode_passed_idx
    on public.submissions (problem_id, mode, passed);

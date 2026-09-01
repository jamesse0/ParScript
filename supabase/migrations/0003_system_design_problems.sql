-- 4th problem category ('system_design') + a pytest-based grading path.
--
-- Existing I/O-pair problems are untouched: test_kind backfills to 'io_pairs'
-- via the column default, test_file stays null, and the payload check passes
-- because every existing row has test_cases.

-- 1. widen the difficulty check (the inline check from 0001_init is auto-named
--    problems_difficulty_check by Postgres).
alter table public.problems drop constraint if exists problems_difficulty_check;
alter table public.problems
    add constraint problems_difficulty_check
    check (difficulty in ('easy', 'medium', 'hard', 'system_design'));

-- 2. execution discriminator: 'io_pairs' = compare run_code(*args) == expected;
--    'pytest' = run a hidden pytest module against the submitted solution.
alter table public.problems
    add column if not exists test_kind text not null default 'io_pairs'
    check (test_kind in ('io_pairs', 'pytest'));

-- 3. the hidden pytest grading module source (only for test_kind = 'pytest').
--    Never returned to the client -- see dataaccess/problems.py.
alter table public.problems
    add column if not exists test_file text;

-- 4. test_cases is meaningless for pytest problems.
alter table public.problems
    alter column test_cases drop not null;

-- 5. integrity: each kind must carry its own grading payload.
alter table public.problems drop constraint if exists problems_grading_payload_check;
alter table public.problems
    add constraint problems_grading_payload_check
    check (
        (test_kind = 'io_pairs' and test_cases is not null)
        or (test_kind = 'pytest'  and test_file  is not null)
    );

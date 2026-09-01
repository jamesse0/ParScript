-- /chat now records the model's reasoning cost and a short reasoning summary
-- per attempt (Responses API). Existing rows backfill to 0 / NULL.

alter table public.attempts
    add column if not exists reasoning_tokens integer not null default 0;

alter table public.attempts
    add column if not exists reasoning_summary text;

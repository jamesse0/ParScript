# Booking Service — example prompts

Reference prompts for the **Grow a Booking Service** course
(`grow-a-booking-service`). Scored on _total tokens across all four steps_; every
step starts from **your own** previous solution and re-runs the earlier tests.

The winning move: in step 1, store bookings **per room** and factor out two
private helpers —

- one that tests whether an interval overlaps a room's bookings (or just lean on
  `is_free`), and
- one that records a booking.

Then every later step is "check with the helper, then record with the helper" —
no new interval math, no touching `book`.

---

## Step 1 — Reservations (`booking-1-basics`)

> Implement a class `Calendar` in one file. Times are integers; a slot is the
> half-open interval `[start, end)`, so `[9, 10)` and `[10, 11)` do **not**
> overlap.
>
> - `book(room, start, end)` — reserve the slot for that room; raise `ValueError`
>   if it overlaps an existing booking for that room.
> - `is_free(room, start, end)` — `True` if nothing booked for that room overlaps
>   `[start, end)`.
>
> Rooms are independent. Store bookings **per room**, and factor out two private
> helpers: one that tests whether an interval overlaps that room's bookings, one
> that records a booking. `book` should just be "check, then record." Later steps
> extend this same class.

**Why it's good:** the per-room store + the two helpers are the whole game — steps
2–4 are all built out of them. Stating the half-open convention up front also
avoids a wrong guess on the boundary case.

**Anti-pattern (costs you later):** one flat list of `(room, start, end)` tuples
scanned inline in `book`, with the overlap comparison written out by hand. It
passes step 1 for the same price, but step 3 then has to re-derive that
comparison and step 4 can't cheaply ask "does this fit?".

---

## Step 2 — Cancel & List (`booking-2-cancel`)

_(editor is pre-filled with your step-1 code)_

> Add two methods; `book` / `is_free` stay exactly as they are.
>
> - `cancel(room, start)` — remove that room's booking that starts at `start`;
>   raise `KeyError` if there's no booking starting there.
> - `bookings(room)` — that room's bookings as `(start, end)` tuples, earliest
>   first; unknown room → `[]`.
>
> Both are plain reads/writes of the per-room store from step 1 — don't touch the
> overlap logic.

**Why it's good:** points the model straight at the step-1 data structure and
fences off everything else, so it adds ~10 lines instead of regenerating the file.

---

## Step 3 — Recurring (`booking-3-recurring`)

_(editor is pre-filled with your step-2 code)_

> Add `book_recurring(room, start, end, count, period)`: book `count` occurrences,
> where occurrence `i` spans `[start + i*period, end + i*period)`. All-or-nothing
> — if **any** occurrence would overlap an existing booking, book none of them and
> raise `ValueError`.
>
> Two passes over your step-1 helpers: check every occurrence for overlap first,
> then record them all. Add no new interval math.

**Why it's good:** "two passes over your existing helpers" is only cheap if step 1
actually exposed a check helper and a record helper. If it didn't, the model has
to re-implement overlap detection here — which is exactly the maintainability cost
the step measures.

---

## Step 4 — Waitlist (`booking-4-waitlist`)

_(editor is pre-filled with your step-3 code)_

> Add a waitlist.
>
> - `waitlist(room, start, end)` — register interest in a slot for that room;
>   don't book anything now.
> - `cancel(room, start)` — after removing the booking, try to promote: take the
>   **earliest-start** waitlisted request for that room that now fits (reuse
>   `is_free`), book it, drop it from the waitlist, and return its `(start, end)`.
>   Return `None` if nothing fits. A missing booking still raises `KeyError`.
>
> The waitlist is a second per-room list alongside the bookings; promotion is
> `is_free` + your record helper. Don't rewrite `cancel` from scratch — extend it.

**Why it's good:** promotion is a three-liner _if_ `is_free` and the record helper
already exist and rooms are already keyed. Every earlier shortcut shows up here as
extra tokens re-deriving "does this slot fit now that one booking is gone?".

---

## General tips

- **Front-load the whole contract.** One complete prompt beats three
  back-and-forths — every reply re-sends the growing code as context.
- **Name the seam, not the solution.** "Two passes over your existing helpers"
  costs far less than pasting a diff or re-describing the file.
- **Say "don't touch X".** Fencing off `book` / the overlap logic stops the model
  from helpfully rewriting parts that already pass.
- **Ask for the structure in step 1.** Per-room storage + a check helper + a
  record helper is the cheapest maintainability you'll ever buy; you pay for its
  absence in every later step.

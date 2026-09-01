# Notification Dispatcher — example prompts

Reference prompts for the **Grow a Notification Dispatcher** course
(`grow-a-notification-dispatcher`). The course scores you on *total tokens across
all four steps*, and every step starts from **your own** previous solution. So a
good step-1 prompt doesn't just solve step 1 cheaply — it asks for a structure
that makes steps 2–4 one-line diffs instead of rewrites.

The winning move: **one formatting/delivery unit per channel, looked up by name**
(a dict registry, or a small class per channel). Every later step then plugs into
that unit instead of editing `send()`.

Token counts below are rough (gpt-5-class tokenizer), for calibration only.

---

## Step 1 — Core (`notif-dispatch-1-core`)

> Implement `Notification`, `User`, and `Dispatcher` in one file.
>
> - `Notification(message, priority="normal")` — priority is `"normal"` or `"urgent"`.
> - `User(name, channels, dnd=False)` — `channels` is an ordered list of channel names.
> - `Dispatcher.send(user, notification)` returns `[{"channel", "message"}]`, one per
>   channel, in `user.channels` order.
>
> Structure the per-channel formatting as a **registry keyed by channel name** —
> a dict `{name: formatter}` or one small class per channel — so adding a channel
> later is a single new entry and touches nothing else. Formatters:
> `email` → message unchanged; `sms` → `message[:20]`; `push` → `"🔔 " + message`.
>
> - Unknown channel name → raise `ValueError`.
> - If `user.dnd` is set and `notification.priority != "urgent"` → return `[]`.
> - `Dispatcher` holds no state between calls.

**Why it's good:** complete spec in one turn, no follow-ups needed, and the
"registry keyed by channel name" sentence is what makes the rest of the course
cheap. ~180 tokens in.

**Anti-pattern (costs you later):** "use an if/elif on the channel name inside
`send`". Solves step 1 for the same price, but every later step then has to
re-open and re-reason about that conditional.

---

## Step 2 — Slack (`notif-dispatch-2-slack`)

*(editor is pre-filled with your step-1 code; the AI gets it as context)*

> Add a `"slack"` channel. Format: `"*" + message + "*"` (Slack bold).
>
> Add it as one entry in the existing channel registry — don't modify the other
> channels or the `send()` flow. All step-1 behavior stays as-is.

**Why it's good:** names the exact seam ("one entry in the existing registry")
so the model makes a surgical change instead of regenerating the file. If step 1
was well-factored this is ~40 tokens in and a ~15-line diff out.

---

## Step 3 — Categories (`notif-dispatch-3-category`)

*(editor is pre-filled with your step-2 code)*

> `Notification` gains an optional `category` string. When it's set, each channel
> prefixes it in that channel's own style; when it's not, formatting is unchanged.
> With `category="Deploys"` and message `m`:
>
> - email → `"[Deploys] " + m`
> - push → `"🔔 [Deploys] " + m`
> - slack → `"*[Deploys]* " + m`
> - sms → `"Deploys: " + m`, then the existing 20-char cap applies to the whole string
>
> Fold the prefix into each channel's own formatter — don't special-case
> `category` inside `send()`.

**Why it's good:** `category` is a cross-cutting concern every channel has to
apply. If step 1 gave each channel its own formatter, this is one small edit per
formatter; if formatting was one `if/elif` chain, `category` now has to be
threaded through every branch. Same discriminator as a new channel, but along a
different axis.

---

## Step 4 — Digest (`notif-dispatch-4-digest`)

> Add opt-in digest mode.
>
> - `User(..., digest_size=N)`. For a digest user, `send()` appends the
>   notification to a per-user queue and returns `[]`; when the queue length
>   reaches `N`, flush it.
> - `flush(user)` force-flushes a partial batch.
> - Flushing joins the queued messages with `"\n"` into one combined message,
>   runs that through the **existing** per-channel formatting, clears the queue,
>   and returns the result list.
> - Non-digest users: completely unchanged.
>
> Implement this as a **queueing layer in front of** the current delivery path —
> wrap it, don't edit it. `send()` decides "queue or deliver now"; the per-channel
> formatting stays exactly as it is.

**Why it's good:** frames the change as "wrap, don't edit", which is only cheap
if steps 1–3 kept "decide to send" separate from "format for a channel". If they
didn't, expect the model to need a bigger rewrite here — that gap is exactly what
step 4 is designed to expose.

---

## General tips

- **Front-load the whole contract.** One complete prompt beats three
  back-and-forths — each reply re-sends the growing code as context.
- **Name the seam, not the solution.** "Add one entry to the registry" costs far
  fewer tokens (in and out) than pasting a diff or re-describing the file.
- **Say "don't touch X".** Explicitly fencing off the working code stops the
  model from helpfully rewriting parts that already pass.
- **Ask for the structure in step 1.** It's the cheapest place to buy
  maintainability; you pay for the lack of it in every later step.

"""Request/response models = the API contract from DESIGN.md §5.

DRAFT. Confirm exact field names/shapes at the 15-minute sync (DESIGN.md §8)
before splitting off; all three backend areas and the frontend build against this.
"""

from typing import Literal

from pydantic import BaseModel

# --- shared -----------------------------------------------------------------


class TestResult(BaseModel):
    input: object
    expected_output: object
    actual_output: object | None = None
    passed: bool


# --- POST /chat -----------------------------------------------------------


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    problem_id: str
    message_history: list[ChatMessage]


class ChatResponse(BaseModel):
    reply: str
    code: str
    input_tokens: int
    output_tokens: int  # includes reasoning_tokens (Responses API accounting)
    # hidden thinking tokens the model spent before answering (part of
    # output_tokens); a high value on a simple ask = a vague prompt.
    reasoning_tokens: int = 0
    # short natural-language gist of the model's reasoning ("" if none) --
    # not the raw chain-of-thought, which OpenAI never exposes.
    reasoning_summary: str = ""
    # id of the attempts row recorded for this chat call (routes/chat.py must
    # insert one per call via dataaccess.attempts.insert_attempt).
    attempt_id: str


# --- POST /submit -------------------------------------------------------


class SubmitRequest(BaseModel):
    problem_id: str
    code: str
    input_tokens: int
    output_tokens: int
    elapsed_seconds: float
    # the chat attempt this code came from, if the user didn't hand-write it
    attempt_id: str | None = None
    # "prompt" = AI-assisted run; "manual" = hand-written, ranked by time,
    # excluded from /me/metrics.
    mode: Literal["prompt", "manual"] = "prompt"


class SubmitResponse(BaseModel):
    passed: bool
    test_results: list[TestResult]
    # id of the submissions row recorded for this Run-tests click
    submission_id: str
    # echoes SubmitRequest.attempt_id when the tested code came from a chat attempt
    attempt_id: str | None = None


# --- POST /review -----------------------------------------------------


class ReviewRequest(BaseModel):
    problem_id: str
    code: str


class ReviewResponse(BaseModel):
    time_complexity: str
    space_complexity: str
    comments: list[str]


# --- GET /problems ---------------------------------------------------


class ProblemSummary(BaseModel):
    id: int
    slug: str
    title: str
    difficulty: str  # "easy" | "medium" | "hard" | "system_design"
    par_tokens: int


class ProblemDetail(ProblemSummary):
    description: str
    function_signature: str
    starter_code: str
    # "io_pairs" -> compare run_code(*args) == expected; "pytest" -> hidden
    # pytest module (system_design). The grading test_file is never sent.
    test_kind: str = "io_pairs"
    test_cases: list[dict] | None = None  # [{input, expected_output}]; null for pytest problems


# --- GET /leaderboard/{problem_id} --------------------------------


class LeaderboardRow(BaseModel):
    username: str
    user_id: str
    submission_id: str  # the score's winning submission -- key for GET /submissions/{id}/prompts
    total_input_tokens: int
    total_output_tokens: int
    elapsed_seconds: float
    created_at: str


class PromptTraceResponse(BaseModel):
    """The chat prompts behind one leaderboard score. Only returned to users who
    have themselves passed the problem (or own the score). View-only -- the
    frontend renders it non-selectable."""
    username: str
    has_trace: bool  # False when the run was hand-written / edited (no attempt)
    prompts: list[str]  # the author's chat messages, in order
    model: str | None = None
    created_at: str | None = None


# --- GET /leaderboard/global ---------------------------------------


class GlobalLeaderboardRow(BaseModel):
    username: str
    handicap: float  # avg tokens-vs-par ratio across solved problems, lower is better
    problems_solved: int


# --- GET /me/metrics --------------------------------------------


class MetricsHistoryRow(BaseModel):
    problem_title: str
    total_tokens: int
    par_tokens: int
    elapsed_seconds: float
    passed: bool
    created_at: str


class MetricsResponse(BaseModel):
    total_solved: int
    avg_tokens_vs_par: float
    avg_tokens_vs_par_by_difficulty: dict[str, float]
    history: list[MetricsHistoryRow]


# --- courses (maintainability sequences) ---------------------------


class CourseStep(BaseModel):
    position: int
    problem_id: int
    title: str
    par_tokens: int


class CourseSummary(BaseModel):
    slug: str
    title: str
    description: str
    step_count: int
    par_tokens: int  # summed par across the sequence


class CourseDetail(CourseSummary):
    steps: list[CourseStep]


class CourseCompleteRequest(BaseModel):
    # the winning (passing) submission id for each step of the run
    submission_ids: list[str]


class CourseCompletionResponse(BaseModel):
    total_input_tokens: int
    total_output_tokens: int
    elapsed_seconds: float
    par_tokens: int  # summed par for the course
    completed_at: str


class CourseLeaderboardRow(BaseModel):
    username: str
    user_id: str
    total_input_tokens: int
    total_output_tokens: int
    elapsed_seconds: float
    completed_at: str


# --- profiles / onboarding (DESIGN.md §4, §7) -----------------------


class OnboardRequest(BaseModel):
    username: str


class MeResponse(BaseModel):
    id: str
    username: str
    created_at: str

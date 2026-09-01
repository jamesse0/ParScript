"""Request/response models = the API contract from DESIGN.md §5.

DRAFT. Confirm exact field names/shapes at the 15-minute sync (DESIGN.md §8)
before splitting off; all three backend areas and the frontend build against this.
"""

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
    output_tokens: int
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
    difficulty: str  # "easy" | "medium" | "hard"
    par_tokens: int


class ProblemDetail(ProblemSummary):
    description: str
    function_signature: str
    starter_code: str
    test_cases: list[dict]  # [{input, expected_output}]


# --- GET /leaderboard/{problem_id} --------------------------------


class LeaderboardRow(BaseModel):
    username: str
    total_input_tokens: int
    total_output_tokens: int
    elapsed_seconds: float
    created_at: str


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


# --- profiles / onboarding (DESIGN.md §4, §7) -----------------------


class OnboardRequest(BaseModel):
    username: str


class MeResponse(BaseModel):
    id: str
    username: str
    created_at: str

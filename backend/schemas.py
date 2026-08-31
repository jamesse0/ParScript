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


# --- POST /submit -------------------------------------------------------


class SubmitRequest(BaseModel):
    problem_id: str
    code: str
    input_tokens: int
    output_tokens: int
    elapsed_seconds: float


class SubmitResponse(BaseModel):
    passed: bool
    test_results: list[TestResult]
    attempt_id: str


# --- POST /review -----------------------------------------------------


class ReviewRequest(BaseModel):
    problem_id: str
    code: str


class ReviewResponse(BaseModel):
    comments: str


# --- GET /problems ---------------------------------------------------


class ProblemSummary(BaseModel):
    id: str
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

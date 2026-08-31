"""Chat endpoint — OpenAI glue (DESIGN.md §5).

Owner: Full-stack generalist (DESIGN.md §8.3). Implemented against services/openai_client.py.

  POST /chat  {problem_id, message_history}
    -> {reply, code, input_tokens, output_tokens, attempt_id}

Authed: every call records one `attempts` row (the chat history + returned code +
this call's tokens) for reproducibility -- see supabase/migrations/0001_init.sql.
Tokens are accumulated client-side for the live counter; no server-side ledger.
"""

from fastapi import APIRouter, Depends, HTTPException

from config import settings
from dataaccess.attempts import insert_attempt
from dataaccess.problems import get_problem
from deps import require_profile
from schemas import ChatRequest, ChatResponse
from services.openai_client import OpenAICallError, chat_completion

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(body: ChatRequest, user=Depends(require_profile)) -> ChatResponse:
    # Validate the problem_id (workspace context + attempts FK). The problem
    # text is deliberately NOT sent to the model -- see services/openai_client.py.
    problem = get_problem(body.problem_id)
    if problem is None:
        raise HTTPException(status_code=404, detail="problem not found")

    history = [m.model_dump() for m in body.message_history]
    if not history or history[-1]["role"] != "user":
        raise HTTPException(status_code=422, detail="message_history must end with a user message")

    try:
        reply, code, input_tokens, output_tokens = await chat_completion(history)
    except OpenAICallError as exc:
        raise HTTPException(status_code=502, detail=f"OpenAI call failed: {exc}")

    attempt = insert_attempt(
        user_id=user["id"],
        problem_id=problem["id"],
        message_history=history,
        reply=reply,
        code=code,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        model=settings.openai_model,
    )

    return ChatResponse(
        reply=reply,
        code=code,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        attempt_id=attempt["id"],
    )

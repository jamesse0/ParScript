"""Chat endpoint — OpenAI glue (DESIGN.md §5).

Owner: Full-stack generalist (DESIGN.md §8.3). Implement against services/openai_client.py.

  POST /chat  {problem_id, message_history}
    -> {reply, code, input_tokens, output_tokens} for that single call.
  Tokens are accumulated client-side; no server-side session ledger tonight.
"""

from fastapi import APIRouter

router = APIRouter(tags=["chat"])


@router.post("/chat")
async def chat():
    raise NotImplementedError

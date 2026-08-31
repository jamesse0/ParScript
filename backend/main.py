"""ParScript FastAPI entrypoint.

Run from backend/:  uvicorn main:app --reload

Wires every router in routes/. API contract lives in DESIGN.md §5 and schemas.py.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from routes import chat, leaderboard, metrics, problems, review, submit

app = FastAPI(title="ParScript API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(problems.router)
app.include_router(leaderboard.router)
app.include_router(metrics.router)
app.include_router(submit.router)
app.include_router(chat.router)
app.include_router(review.router)


@app.get("/health")
async def health():
    return {"status": "ok"}

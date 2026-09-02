import os

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from ml.model import LeadScoreRequest, score_lead
from rag.qa import get_assistant

app = FastAPI(title="MGC Sales Assistant API", version="1.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3)


@app.get("/health")
def health():
    return {
        "status": "ok",
        "rag": {
            "provider": "gemini" if os.getenv("GEMINI_API_KEY", "").strip() else None
        },
    }


@app.post("/api/ask")
def ask_docs(body: AskRequest):
    try:
        result = get_assistant().ask(body.question)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    return {
        "question": body.question,
        "answer": result.answer,
        "sources": result.sources,
        "confidence": result.confidence,
        "mode": result.mode,
    }


@app.post("/api/score")
def score(body: LeadScoreRequest):
    try:
        return score_lead(body)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/examples")
def examples():
    return {
        "questions": [
            "What's the base price of a 2-bed in Block B?",
            "What's the total for a Margalla-facing corner unit on floor 15, 2-bed Block B?",
            "What's the transfer fee?",
            "What's the rental yield on a 1-bed?",
            "Who is the anchor tenant?",
            "What amenities does Aurora Heights have?",
            "When is possession for Block A?",
        ]
    }

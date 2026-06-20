import os
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "budget_app.settings")

import django

django.setup()

from ai_Chat_bot.ai_part.ai_chat import build_agent
from ai_Chat_bot.ai_part.db_utils import (
    generate_session_id,
    get_chat_history_by_user,
    init_db,
    load_history,
    save_history,
    create_session,
)
from budget_transactions.models import BudgetTransactionBucket
from budget_users.models import BudgetUser

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    phone_number: str = Field(min_length=5, max_length=20)
    message: str = Field(min_length=1)
    session_id: str | None = None


class ChatResponse(BaseModel):
    phone_number: str
    session_id: str
    response: str


class ChatMessageHistoryResponse(BaseModel):
    phone_number: str
    sessions: list[dict]


@router.post("", response_model=ChatResponse)
def chat_with_budget_assistant(payload: ChatRequest):
    init_db()

    try:
        user = BudgetUser.objects.get(phone_number=payload.phone_number)
    except BudgetUser.DoesNotExist as exc:
        raise HTTPException(status_code=404, detail="User not found.") from exc

    try:
        api_key = user.llm_api_key.get_api_key()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="Saved LLM API key is missing or unreadable.") from exc

    try:
        transactions = list(user.transaction_bucket.transactions)
    except BudgetTransactionBucket.DoesNotExist:
        transactions = []

    agent = build_agent(api_key=api_key, transactions=transactions, phone_number=user.phone_number)
    session_id = payload.session_id or generate_session_id(payload.message, user.phone_number)
    create_session(session_id, user.phone_number)
    messages = load_history(session_id)
    transaction_context = f"Current user transaction JSON: {transactions}"
    result = agent.run_sync(f"{transaction_context}\n\nUser message: {payload.message}", message_history=messages)
    messages.extend(result.new_messages())
    save_history(session_id, messages)
    return ChatResponse(phone_number=user.phone_number, session_id=session_id, response=str(result.output))


@router.get("/history/{phone_number}", response_model=ChatMessageHistoryResponse)
def get_chat_history(phone_number: str):
    init_db()

    try:
        user = BudgetUser.objects.get(phone_number=phone_number)
    except BudgetUser.DoesNotExist as exc:
        raise HTTPException(status_code=404, detail="User not found.") from exc

    return ChatMessageHistoryResponse(phone_number=user.phone_number, sessions=get_chat_history_by_user(user.phone_number))

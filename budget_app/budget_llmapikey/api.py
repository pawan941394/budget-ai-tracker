import os
import sys
from pathlib import Path

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "budget_app.settings")

import django

django.setup()

from budget_llmapikey.models import Llmapikey
from budget_users.models import BudgetUser

router = APIRouter(prefix="/llm-api-keys", tags=["llm-api-keys"])


class LlmApiKeyCreateRequest(BaseModel):
    phone_number: str = Field(min_length=5, max_length=20)
    provider: str = Field(default="openai", min_length=1, max_length=100)
    api_key: str = Field(min_length=1)


class LlmApiKeyResponse(BaseModel):
    id: int
    user_id: int
    phone_number: str
    provider: str
    is_active: bool
    api_key_hashed: bool


@router.post("/upsert", response_model=LlmApiKeyResponse)
def upsert_llm_api_key(payload: LlmApiKeyCreateRequest):
    try:
        user = BudgetUser.objects.get(phone_number=payload.phone_number)
    except BudgetUser.DoesNotExist as exc:
        raise HTTPException(status_code=404, detail="User not found.") from exc

    key_entry, _ = Llmapikey.objects.update_or_create(
        user=user,
        provider=payload.provider,
        defaults={
            "api_key": payload.api_key,
            "is_active": True,
        },
    )

    return LlmApiKeyResponse(
        id=key_entry.id,
        user_id=user.id,
        phone_number=user.phone_number,
        provider=key_entry.provider,
        is_active=key_entry.is_active,
        api_key_hashed=key_entry.api_key.startswith("pbkdf2_"),
    )


@router.get("/{phone_number}", response_model=LlmApiKeyResponse)
def get_llm_api_key(phone_number: str):
    try:
        user = BudgetUser.objects.get(phone_number=phone_number)
    except BudgetUser.DoesNotExist as exc:
        raise HTTPException(status_code=404, detail="User not found.") from exc

    try:
        key = user.llm_api_key
    except Llmapikey.DoesNotExist as exc:
        raise HTTPException(status_code=404, detail="LLM API key not found.") from exc

    return LlmApiKeyResponse(
        id=key.id,
        user_id=user.id,
        phone_number=user.phone_number,
        provider=key.provider,
        is_active=key.is_active,
        api_key_hashed=key.api_key.startswith("pbkdf2_"),
    )


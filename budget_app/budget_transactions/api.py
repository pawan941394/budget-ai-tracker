import os
import sys
import tempfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pydantic import BaseModel, Field
from cryptography.fernet import InvalidToken

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "budget_app.settings")

import django

django.setup()

from .ocr_Codes import get_transaction_data
from budget_transactions.models import BudgetTransactionBucket
from budget_users.models import BudgetUser

router = APIRouter(prefix="/transactions", tags=["transactions"])


class TransactionData(BaseModel):
    status: str | None = None
    amount: float | None = None
    sender_name: str | None = None
    sender_upi: str | None = None
    receiver_name: str | None = None
    receiver_upi: str | None = None
    bank: str | None = None
    timestamp: str | None = None
    reference_id: str | None = None
    payment_type: str | None = None
    utr_id: str | None = None


class TransactionUpsertRequest(BaseModel):
    phone_number: str = Field(min_length=5, max_length=20)
    transaction: TransactionData


class TransactionBucketResponse(BaseModel):
    user_id: int
    phone_number: str
    transactions: list[TransactionData]


@router.post("/upsert", response_model=TransactionBucketResponse)
def upsert_transaction(payload: TransactionUpsertRequest):
    try:
        user = BudgetUser.objects.get(phone_number=payload.phone_number)
    except BudgetUser.DoesNotExist as exc:
        raise HTTPException(status_code=404, detail="User not found.") from exc

    bucket, _ = BudgetTransactionBucket.objects.get_or_create(user=user, defaults={"transactions": []})
    bucket.transactions.append(payload.transaction.model_dump())
    bucket.save(update_fields=["transactions", "updated_at"])

    return TransactionBucketResponse(
        user_id=user.id,
        phone_number=user.phone_number,
        transactions=[TransactionData(**item) for item in bucket.transactions],
    )


@router.get("/{phone_number}", response_model=TransactionBucketResponse)
def get_transactions(phone_number: str):
    try:
        user = BudgetUser.objects.get(phone_number=phone_number)
    except BudgetUser.DoesNotExist as exc:
        raise HTTPException(status_code=404, detail="User not found.") from exc

    try:
        bucket = user.transaction_bucket
    except BudgetTransactionBucket.DoesNotExist:
        return TransactionBucketResponse(user_id=user.id, phone_number=user.phone_number, transactions=[])

    return TransactionBucketResponse(
        user_id=user.id,
        phone_number=user.phone_number,
        transactions=[TransactionData(**item) for item in bucket.transactions],
    )


@router.post("/upload", response_model=TransactionBucketResponse)
def upload_transaction_image(
    phone_number: str = Form(...),
    image: UploadFile = File(...),
):
    try:
        user = BudgetUser.objects.get(phone_number=phone_number)
    except BudgetUser.DoesNotExist as exc:
        raise HTTPException(status_code=404, detail="User not found.") from exc

    try:
        api_key = user.llm_api_key.get_api_key()
    except AttributeError as exc:
        raise HTTPException(status_code=400, detail="No saved LLM API key found for this user.") from exc
    except InvalidToken as exc:
        raise HTTPException(
            status_code=400,
            detail="The saved API key is in an old hashed format. Please re-save the LLM API key once.",
        ) from exc

    suffix = Path(image.filename or "").suffix or ".png"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
        temp_file.write(image.file.read())
        temp_path = temp_file.name

    try:
        parsed_transaction = get_transaction_data(temp_path, api_key=api_key)
    finally:
        try:
            os.remove(temp_path)
        except OSError:
            pass

    return TransactionBucketResponse(
        user_id=user.id,
        phone_number=user.phone_number,
        transactions=[TransactionData(**parsed_transaction.model_dump())],
    )

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from budget_users.models import BudgetUser

router = APIRouter(prefix="/users", tags=["users"])


class UserCreateRequest(BaseModel):
    phone_number: str = Field(min_length=5, max_length=20)
    password: str = Field(min_length=8, max_length=128)


class UserCreateResponse(BaseModel):
    id: int
    phone_number: str


@router.post("/register", response_model=UserCreateResponse, status_code=201)
def create_user(payload: UserCreateRequest):
    if BudgetUser.objects.filter(phone_number=payload.phone_number).exists():
        raise HTTPException(status_code=400, detail="A user with this phone number already exists.")

    user = BudgetUser.objects.create_user(
        phone_number=payload.phone_number,
        password=payload.password,
    )
    return UserCreateResponse(id=user.id, phone_number=user.phone_number)

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config.database import get_db
from backend.models.investor import AccreditationType, Investor, InvestorStatus
from backend.services.encryption import encrypt, hash_email

router = APIRouter()


class InvestorIntakeRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=200)
    email: EmailStr
    phone: str | None = Field(default=None, max_length=20)
    accreditation_type: AccreditationType


class InvestorIntakeResponse(BaseModel):
    id: str
    status: InvestorStatus
    message: str


@router.post("/intake", response_model=InvestorIntakeResponse, status_code=201)
async def investor_intake(
    body: InvestorIntakeRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    email_h = hash_email(body.email)

    existing = await db.execute(
        select(Investor).where(Investor.email_hash == email_h)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=409,
            detail="An application with this email already exists.",
        )

    investor = Investor(
        encrypted_name=encrypt(body.full_name),
        encrypted_email=encrypt(body.email),
        encrypted_phone=encrypt(body.phone) if body.phone else None,
        email_hash=email_h,
        accreditation_type=body.accreditation_type,
        status=InvestorStatus.PENDING,
        intake_ip=request.client.host if request.client else None,
    )
    db.add(investor)
    await db.commit()
    await db.refresh(investor)

    return InvestorIntakeResponse(
        id=investor.id,
        status=investor.status,
        message="Application received. You will be contacted for verification documents.",
    )

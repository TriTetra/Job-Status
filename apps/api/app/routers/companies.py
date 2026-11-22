"""Companies router."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy.orm import Session

from ..dependencies import get_db_session, get_user_id
from ..schemas.company import CompanyMemoryResponse, CompanyResponse
from careeros.companies import logos
from careeros.companies.directory import company_detail, company_directory
from careeros.companies.repositories.company_repo import CompanyMemoryRepository, CompanyRepository

router = APIRouter()


@router.get("/", response_model=List[CompanyResponse])
def list_companies(
    tier: Optional[str] = Query(None, description="Filter by tier (big_tech, large, startup, unknown)"),
    session: Session = Depends(get_db_session),
):
    """List companies, optionally filtered by tier."""
    repo = CompanyRepository(session)
    companies = repo.get_by_tier(tier) if tier else repo.get_all()
    return [CompanyResponse.model_validate(c) for c in companies]


@router.get("/hiring", response_model=List[CompanyResponse])
def companies_hiring_now(
    limit: int = Query(20, le=50),
    session: Session = Depends(get_db_session),
):
    """Companies actively hiring (hiring_trend = up/spike)."""
    repo = CompanyRepository(session)
    return [CompanyResponse.model_validate(c) for c in repo.get_hiring_now(limit=limit)]


@router.get("/logo/{key}", summary="A board company's logo (cached)")
def company_logo(key: str, user_id: str = Depends(get_user_id)):
    """The logo image, or 404 (the web then shows a monogram). Browsers keep it for a week."""
    found = logos.logo(key)
    if found is None:
        raise HTTPException(status_code=404, detail="No logo")
    data, ctype = found
    return Response(content=data, media_type=ctype, headers={"Cache-Control": "private, max-age=604800"})


@router.get("/boards", summary="Companies from the job boards, with this user's view")
def board_companies(user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    """Every company CareerOS reads a board for: open roles, hiring pace, your matches, skills asked."""
    return {"companies": company_directory(session, user_id)}


@router.get("/boards/{key}", summary="One board company with its open roles")
def board_company(key: str, user_id: str = Depends(get_user_id), session: Session = Depends(get_db_session)):
    detail = company_detail(session, user_id, key)
    if detail is None:
        raise HTTPException(status_code=404, detail="Company not found")
    return detail


@router.get("/{name}/memory", response_model=CompanyMemoryResponse)
def get_company_memory(
    name: str,
    user_id: str = Depends(get_user_id),
    session: Session = Depends(get_db_session),
):
    """User's history with a specific company."""
    repo = CompanyMemoryRepository(session)
    summary = repo.get_company_summary(user_id=user_id, company_name=name)
    return CompanyMemoryResponse(company=name, **summary)


@router.get("/{name}", response_model=CompanyResponse)
def get_company(
    name: str,
    session: Session = Depends(get_db_session),
):
    """Get company profile."""
    repo = CompanyRepository(session)
    company = repo.get(name=name)
    if not company:
        raise HTTPException(status_code=404, detail=f"Company '{name}' not found")
    return CompanyResponse.model_validate(company)


@router.post("/track", response_model=CompanyResponse, status_code=201)
def track_company(
    name: str = Query(..., min_length=1, max_length=200),
    session: Session = Depends(get_db_session),
):
    """Add a company to the watchlist (idempotent — returns existing if already tracked)."""
    repo = CompanyRepository(session)
    company = repo.get_or_create(name=name)
    session.commit()
    return CompanyResponse.model_validate(company)


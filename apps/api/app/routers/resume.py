"""Resume generation router."""

from fastapi import APIRouter, Depends, HTTPException

from ..dependencies import get_user_id

from ..schemas.resume import ResumeGenerateRequest, ResumeGenerateResponse

router = APIRouter()


@router.post("/generate", response_model=ResumeGenerateResponse)
def generate_resume(
    request: ResumeGenerateRequest,
    user_id: str = Depends(get_user_id),
):
    """Generate a target-aware resume."""
    try:
        from pathlib import Path
        from careeros.resume.resume_generator import generate_resume as _gen

        output_path: Path = _gen(
            target_company=request.target_company,
            target_title=request.target_title,
            template_name=request.template_name,
            job_description=request.job_description,
            user_id=user_id,
        )
        content = output_path.read_text(encoding="utf-8")
        return ResumeGenerateResponse(
            output_path=str(output_path),
            target_company=request.target_company,
            target_title=request.target_title,
            template_used=request.template_name,
            size_chars=len(content),
            lines=len(content.splitlines()),
        )
    except ImportError as e:
        raise HTTPException(status_code=501, detail=f"Resume generator not available: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

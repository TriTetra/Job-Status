"""Resume generation router."""

import logging

from fastapi import APIRouter, Depends, HTTPException

from careeros.shared.llm import LLMBudgetExceeded, LLMError, LLMNotConfiguredError

from ..dependencies import get_user_id

from ..schemas.resume import ResumeGenerateRequest, ResumeGenerateResponse

router = APIRouter()
logger = logging.getLogger(__name__)


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
    except LLMBudgetExceeded as e:
        raise HTTPException(status_code=429, detail=str(e))
    except LLMNotConfiguredError:
        raise HTTPException(status_code=503, detail="The AI service isn't configured on this server")
    except LLMError:
        logger.exception("Resume generation: LLM failed for %s", user_id)
        raise HTTPException(status_code=502, detail="The AI service failed — try again in a minute")
    except Exception:
        logger.exception("Resume generation failed for %s", user_id)
        raise HTTPException(status_code=500, detail="Resume generation failed")

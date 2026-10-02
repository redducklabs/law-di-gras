"""Cases landing page API. Real rows come from Clio (GET only) + cached Dashboards;
rows with sample=true are fictional demo filler from app/cases/samples.json."""

from fastapi import APIRouter

from app.cases.rows import case_rows
from app.schemas import CaseRow

router = APIRouter(tags=["cases"])


@router.get("/api/cases", response_model=list[CaseRow])
def cases(samples: bool = True):
    return case_rows(include_samples=samples)

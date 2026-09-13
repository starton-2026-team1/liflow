from fastapi import APIRouter, Query

from app.schemas.welfare_benefit import WelfareBenefitResponse
from app.services.welfare_benefit_service import list_welfare_benefits

router = APIRouter()


@router.get("", response_model=list[WelfareBenefitResponse])
async def get_welfare_benefits(
    ctpv_name: str | None = Query(default=None, max_length=30),
    sgg_name: str | None = Query(default=None, max_length=30),
) -> list[WelfareBenefitResponse]:
    return await list_welfare_benefits(ctpv_name=ctpv_name, sgg_name=sgg_name)

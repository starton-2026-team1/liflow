import asyncio
import time
from xml.etree import ElementTree

import httpx

from app.core.config import settings
from app.core.errors import AppError, ErrorCode
from app.schemas.welfare_benefit import WelfareBenefitResponse

LOCAL_LIST_URL = "https://apis.data.go.kr/B554287/LocalGovernmentWelfareInformations/LcgvWelfarelist"
CACHE_SECONDS = 6 * 60 * 60
_cache: dict[str, tuple[float, list[WelfareBenefitResponse]]] = {}
_cache_lock = asyncio.Lock()


def _text(element: ElementTree.Element, *names: str) -> str:
    for name in names:
        child = element.find(f".//{name}")
        if child is not None and child.text:
            return child.text.strip()
    return ""


def _category(item: ElementTree.Element) -> str:
    source = " ".join(
        _text(item, name)
        for name in ("intrsThemaNmArray", "servNm", "servDgst", "lifeNmArray")
    )
    if any(word in source for word in ("주거", "임대", "주택")):
        return "주거"
    if any(word in source for word in ("건강", "의료", "검진", "치매")):
        return "건강·의료"
    if any(word in source for word in ("돌봄", "요양", "안전")):
        return "돌봄"
    return "생활지원"


def parse_welfare_xml(content: bytes) -> list[WelfareBenefitResponse]:
    try:
        root = ElementTree.fromstring(content)
    except ElementTree.ParseError as exc:
        raise ValueError("복지서비스 응답을 읽을 수 없습니다.") from exc

    result_code = _text(root, "resultCode", "returnReasonCode")
    if result_code and result_code not in ("00", "0"):
        message = _text(root, "resultMessage", "returnAuthMsg") or "공공데이터 API 요청에 실패했습니다."
        raise ValueError(message)

    items = root.findall(".//servList") or root.findall(".//item")
    benefits = []
    for item in items:
        benefit_id = _text(item, "servId", "serviceId", "서비스ID")
        title = _text(item, "servNm", "serviceName", "서비스명")
        if not benefit_id or not title:
            continue
        benefits.append(
            WelfareBenefitResponse(
                id=benefit_id,
                category=_category(item),
                title=title,
                description=_text(item, "servDgst", "servSummary", "서비스요약") or "자세한 지원 내용을 확인해 보세요.",
                organization=_text(item, "bizChrDeptNm", "jurMnofNm", "jurOrgNm") or "복지로",
                eligibility=_text(item, "lifeNmArray", "trgterIndvdlArray", "sprtTrgtCn") or None,
                application_method=_text(item, "aplyMtdNm", "aplyMtdCn") or None,
                official_url=_text(item, "servDtlLink", "servUrl", "서비스URL") or None,
            )
        )
    return benefits


async def list_welfare_benefits(
    *, ctpv_name: str | None = None, sgg_name: str | None = None
) -> list[WelfareBenefitResponse]:
    if not settings.public_data_service_key:
        raise AppError(ErrorCode.INTERNAL_SERVER_ERROR, "공공데이터 API 키가 설정되지 않았습니다.")

    cache_key = f"{ctpv_name or 'all-local'}:{sgg_name or ''}"
    cached = _cache.get(cache_key)
    if cached and time.monotonic() - cached[0] < CACHE_SECONDS:
        return cached[1]

    params: dict[str, str | int] = {
        "serviceKey": settings.public_data_service_key,
        "callTp": "L",
        "pageNo": 1,
        "numOfRows": 100,
    }
    if ctpv_name:
        params["ctpvNm"] = ctpv_name or ""
        if sgg_name:
            params["sggNm"] = sgg_name

    try:
        async with httpx.AsyncClient(timeout=15) as client:
            for attempt in range(2):
                try:
                    response = await client.get(LOCAL_LIST_URL, params=params)
                    response.raise_for_status()
                    break
                except httpx.HTTPError:
                    if attempt == 1:
                        raise
                    await asyncio.sleep(0.5)
        benefits = parse_welfare_xml(response.content)
    except (httpx.HTTPError, ValueError) as exc:
        raise AppError(
            ErrorCode.INTERNAL_SERVER_ERROR,
            "복지 혜택 정보를 불러오지 못했습니다.",
            detail="복지 정보를 잠시 불러오지 못했어요. 잠시 후 다시 시도해 주세요.",
        ) from exc

    async with _cache_lock:
        _cache[cache_key] = (time.monotonic(), benefits)
    return benefits

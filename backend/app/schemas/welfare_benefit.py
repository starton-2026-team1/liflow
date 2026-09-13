from pydantic import BaseModel


class WelfareBenefitResponse(BaseModel):
    id: str
    category: str
    title: str
    description: str
    organization: str
    eligibility: str | None = None
    application_method: str | None = None
    official_url: str | None = None

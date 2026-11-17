from pydantic import BaseModel, Field


class AnalyticsQuery(BaseModel):
    from_date: str | None = Field(default=None, max_length=10)
    to_date: str | None = Field(default=None, max_length=10)
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    q: str = Field(min_length=1, max_length=500)
    limit: int = Field(default=20, ge=1, le=50)
    session_key: str = Field(default="anonymous", max_length=128)


class SearchResult(BaseModel):
    id: str
    name: str
    category: str
    price: str
    description: str
    image_url: str
    quantity: int
    store_name: str
    score: int
    explanation: list[str]
    alternative_ids: list[str]


class SearchResponse(BaseModel):
    mode: str
    intent: dict
    results: list[SearchResult]
    alternatives: list[SearchResult]


class CopilotRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    conversation_id: str | None = Field(default=None, max_length=128)


class CopilotResponse(BaseModel):
    mode: str
    message: str
    intent: dict
    products: list[SearchResult]
    purchase_executed: bool = False


class CompareRequest(BaseModel):
    product_ids: list[str] = Field(min_length=2, max_length=3)


class SellerToolRequest(BaseModel):
    tool: str = Field(pattern="^(title|description|keywords|category|pricing|campaign|attributes)$")
    product_name: str = Field(min_length=1, max_length=200)
    category: str = Field(default="", max_length=80)
    description: str = Field(default="", max_length=5000)
    price: str = Field(default="", max_length=20)


class PersonalizationRequest(BaseModel):
    enabled: bool
    preferred_categories: list[str] = Field(default_factory=list, max_length=20)

import difflib
import json
import re
import time
from collections import defaultdict, deque
from decimal import Decimal
from threading import Lock

import httpx
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.models import AIResponseLog, AIUsage, Inventory, OrderItem, Product, SearchHistory


CATEGORY_ALIASES = {
    "laptop": "Electronics", "computer": "Electronics", "tv": "Electronics",
    "television": "Electronics", "phone": "Electronics", "headphone": "Electronics",
    "gaming": "Electronics", "shirt": "Fashion", "shoes": "Fashion",
    "fashion": "Fashion", "lamp": "Home", "chair": "Home", "furniture": "Home",
    "skincare": "Beauty", "serum": "Beauty", "running": "Sports",
    "book": "Books", "car": "Automotive", "accessory": "Accessories",
}


class AIProvider:
    def generate(self, operation: str, prompt: str) -> dict:
        settings = get_settings()
        if settings.ai_provider.lower() != "openai-compatible" or not settings.ai_api_url or not settings.ai_api_key:
            return local_ai_output(operation, prompt)

        try:
            response = httpx.post(
                settings.ai_api_url,
                headers={"Authorization": f"Bearer {settings.ai_api_key}", "Content-Type": "application/json"},
                json={
                    "model": settings.ai_model,
                    "messages": [
                        {"role": "system", "content": "Return only valid JSON. Never claim to have executed a purchase or inventory action."},
                        {"role": "user", "content": sanitize_prompt(prompt)},
                    ],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"},
                },
                timeout=settings.ai_timeout_seconds,
            )
            response.raise_for_status()
            content = response.json()["choices"][0]["message"]["content"]
            parsed = json.loads(content)
            if not isinstance(parsed, dict):
                raise ValueError("Provider returned a non-object response")
            return parsed
        except httpx.TimeoutException as exc:
            raise TimeoutError("AI provider timed out") from exc
        except (httpx.HTTPError, KeyError, json.JSONDecodeError, ValueError) as exc:
            raise RuntimeError("AI provider returned an invalid or failed response") from exc


def sanitize_prompt(prompt: str) -> str:
    cleaned = re.sub(r"(?i)(ignore|disregard)\s+(all|any|previous)\s+(instructions|rules)", "[filtered instruction]", prompt)
    return cleaned[:4000]


def extract_intent(query: str) -> dict:
    lowered = sanitize_prompt(query).lower()
    budget_match = re.search(r"(?:under|below|less\s+than|upto|max(?:imum)?|₹|rs\.?\s*)\s*(?:₹|rs\.?\s*)?([\d,]+)\s*(k|lakh|lac)?", lowered)
    budget = None
    if budget_match:
        amount = Decimal(budget_match.group(1).replace(",", ""))
        suffix = budget_match.group(2)
        if suffix == "k":
            amount *= 1000
        elif suffix in {"lakh", "lac"}:
            amount *= 100000
        budget = amount

    category = None
    for term, candidate in CATEGORY_ALIASES.items():
        if term in lowered:
            category = candidate
            break

    specs = []
    for pattern in (r"\b\d+\s*(?:gb|tb)\b", r"\b\d+\s*(?:inch|inch(es)?|mm)\b", r"\b(?:4k|8k|oled|qled|gaming|warranty)\b"):
        specs.extend(re.findall(pattern, lowered))
    return {"category": category, "budget": str(budget) if budget is not None else None, "specifications": specs}


def local_ai_output(operation: str, prompt: str) -> dict:
    intent = extract_intent(prompt)
    if operation == "seller-copy":
        return {
            "label": "LOCAL FALLBACK",
            "title": f"{prompt[:80]} — thoughtfully selected",
            "description": "A clear, factual listing draft generated from the information provided. Verify specifications before publishing.",
            "keywords": sorted(set(re.findall(r"[A-Za-z][A-Za-z0-9]+", prompt.lower())))[:12],
        }
    if operation == "comparison":
        return {"label": "LOCAL FALLBACK", "summary": "Comparison requires actual product records.", "advantages": [], "disadvantages": []}
    return {
        "label": "LOCAL FALLBACK",
        "intent": intent,
        "message": "I can search the actual catalogue using category, budget and text matches. I cannot execute purchases.",
    }


def rank_products(db: Session, query: str, limit: int = 20):
    intent = extract_intent(query)
    lowered = sanitize_prompt(query).lower()
    terms = [term for term in re.findall(r"[a-z0-9]+", lowered) if len(term) >= 2]
    stop = {"i", "need", "want", "looking", "for", "under", "below", "with", "and", "the", "a"}
    terms = [term for term in terms if term not in stop]
    products = db.scalars(select(Product).where(Product.is_active.is_(True))).all()
    budget = Decimal(intent["budget"]) if intent["budget"] else None
    ranked = []
    for product in products:
        if budget is not None and Decimal(str(product.price)) > budget:
            continue
        if intent["category"] and product.category.name != intent["category"]:
            continue
        searchable = f"{product.name} {product.category.name} {product.description} {product.sku}".lower()
        exact_hits = sum(1 for term in terms if term in searchable)
        typo_hits = sum(
            1 for term in terms
            if any(difflib.SequenceMatcher(None, term, word).ratio() >= 0.82 for word in searchable.split())
        )
        score = exact_hits * 3 + typo_hits
        if not terms:
            score = 1
        available = 0
        inv = db.scalar(select(Inventory).where(Inventory.product_id == product.id))
        if inv:
            available = inv.quantity - inv.reserved_quantity
        if available > 0:
            score += 1
        if score > 0:
            reasons = []
            if exact_hits:
                reasons.append(f"Matched {exact_hits} search term(s)")
            if intent["category"]:
                reasons.append(f"Category matches {intent['category']}")
            if budget is not None:
                reasons.append(f"Within ₹{budget:,.2f} budget")
            if available <= 0:
                reasons.append("Currently unavailable")
            ranked.append({
                "product": product,
                "score": score,
                "explanation": reasons or ["Closest textual match"],
                "alternatives": [],
            })
    ranked.sort(key=lambda row: (-row["score"], Decimal(str(row["product"].price))))
    for row in ranked:
        row["alternatives"] = [
            candidate["product"].id
            for candidate in ranked
            if candidate["product"].id != row["product"].id
            and candidate["product"].category_id == row["product"].category_id
        ][:3]
    return ranked[:limit], intent


class InMemoryRateLimiter:
    def __init__(self):
        self.calls: dict[str, deque[float]] = defaultdict(deque)
        self.lock = Lock()

    def allow(self, key: str, limit: int) -> bool:
        now = time.monotonic()
        cutoff = now - 60
        with self.lock:
            queue = self.calls[key]
            while queue and queue[0] < cutoff:
                queue.popleft()
            if len(queue) >= limit:
                return False
            queue.append(now)
            return True


rate_limiter = InMemoryRateLimiter()


def record_ai(
    db: Session,
    user_id: str | None,
    operation: str,
    provider: str,
    model: str,
    started: float,
    success: bool,
    output: dict | None = None,
    error_code: str | None = None,
) -> None:
    db.add(AIUsage(
        user_id=user_id,
        operation=operation,
        provider=provider,
        model=model,
        latency_ms=int((time.monotonic() - started) * 1000),
        success=success,
        error_code=error_code,
    ))
    if output is not None:
        safe_output = json.dumps(output, ensure_ascii=False)
        db.add(AIResponseLog(
            user_id=user_id,
            operation=operation,
            output_json=safe_output,
            sensitive_data_excluded=True,
        ))

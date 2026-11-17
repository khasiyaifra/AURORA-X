import json
import time
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.ai_service import AIProvider, extract_intent, rank_products, record_ai, rate_limiter
from app.config import get_settings
from app.database import get_db
from app.dependencies import get_current_user, require_buyer, require_seller
from app.models import (
    BuyerProfile, Inventory, Order, OrderItem, PersonalizationPreference, Product,
    SearchHistory, SellerOrder, SellerProfile,
)
from app.schemas_ai import (
    CompareRequest, CopilotRequest, CopilotResponse, PersonalizationRequest,
    SearchRequest, SearchResponse, SearchResult, SellerToolRequest,
)

router = APIRouter(prefix="/api/ai", tags=["ai"])
provider = AIProvider()


def ensure_rate_limit(user_id: str | None, request: Request) -> None:
    settings = get_settings()
    key = user_id or request.client.host if request.client else "anonymous"
    if not rate_limiter.allow(key, settings.ai_rate_limit_per_minute):
        raise HTTPException(status_code=status.HTTP_429_TOO_MANY_REQUESTS, detail="AI request limit exceeded")


def serialize_result(db: Session, row: dict) -> SearchResult:
    product = row["product"]
    inventory = db.scalar(select(Inventory).where(Inventory.product_id == product.id))
    quantity = max(inventory.quantity - inventory.reserved_quantity, 0) if inventory else 0
    return SearchResult(
        id=product.id,
        name=product.name,
        category=product.category.name,
        price=f"{Decimal(str(product.price)):.2f}",
        description=product.description,
        image_url=product.image_url,
        quantity=quantity,
        store_name=product.store.name,
        score=row["score"],
        explanation=row["explanation"],
        alternative_ids=row["alternatives"],
    )


@router.post("/search", response_model=SearchResponse)
def intelligent_search(
    payload: SearchRequest,
    request: Request,
    user=Depends(get_current_user) if False else None,
    db: Session = Depends(get_db),
):
    ensure_rate_limit(None, request)
    rows, intent = rank_products(db, payload.q, payload.limit)
    buyer_id = None
    db.add(SearchHistory(
        buyer_id=buyer_id,
        session_key=payload.session_key,
        query=payload.q,
        result_count=len(rows),
    ))
    db.commit()
    results = [serialize_result(db, row) for row in rows]
    alternatives = [serialize_result(db, row) for row in rows[:3]]
    settings = get_settings()
    mode = "external" if settings.ai_provider.lower() == "openai-compatible" and settings.ai_api_url else "deterministic local fallback"
    return SearchResponse(mode=mode, intent=intent, results=results, alternatives=alternatives)


@router.post("/copilot", response_model=CopilotResponse)
def copilot(payload: CopilotRequest, request: Request, user=Depends(require_buyer), db: Session = Depends(get_db)):
    ensure_rate_limit(user.id, request)
    started = time.monotonic()
    rows, intent = rank_products(db, payload.message, 8)
    settings = get_settings()
    mode = "external" if settings.ai_provider.lower() == "openai-compatible" and settings.ai_api_url else "deterministic local fallback"
    message = (
        "I found catalogue products that match your request. "
        "No purchase was made. Review the matches, compare alternatives and add items to your cart only when ready."
    )
    if not rows:
        message = "No actual catalogue products match these constraints. Try broadening the budget or category."
    output = {"message": message, "intent": intent, "purchase_executed": False}
    record_ai(db, user.id, "copilot", settings.ai_provider, settings.ai_model, started, True, output)
    db.commit()
    return CopilotResponse(
        mode=mode,
        message=message,
        intent=intent,
        products=[serialize_result(db, row) for row in rows],
        purchase_executed=False,
    )


@router.post("/compare")
def compare_products(payload: CompareRequest, request: Request, user=Depends(get_current_user), db: Session = Depends(get_db)):
    ensure_rate_limit(user.id, request)
    started = time.monotonic()
    products = db.scalars(select(Product).where(Product.id.in_(payload.product_ids))).all()
    found = {product.id: product for product in products}
    if len(found) != len(set(payload.product_ids)):
        raise HTTPException(status_code=404, detail="One or more products were not found")
    rows = []
    for product_id in payload.product_ids:
        product = found[product_id]
        inventory = db.scalar(select(Inventory).where(Inventory.product_id == product.id))
        quantity = inventory.quantity - inventory.reserved_quantity if inventory else 0
        rows.append({
            "id": product.id,
            "name": product.name,
            "sku": product.sku,
            "category": product.category.name,
            "price": f"{Decimal(str(product.price)):.2f}",
            "description": product.description,
            "available_quantity": max(quantity, 0),
            "seller": product.store.name,
            "delivery": "Not specified",
            "warranty": "Not specified",
            "return_policy": "Not specified",
        })
    cheapest = min(rows, key=lambda row: Decimal(row["price"]))
    output = {
        "mode": "actual catalogue fields only",
        "best_budget": cheapest["id"],
        "best_overall": cheapest["id"],
        "best_specification_match": rows[0]["id"],
        "products": rows,
        "disadvantages": ["Warranty and return policy are not stored in the catalogue."],
    }
    settings = get_settings()
    record_ai(db, user.id, "compare", "local", "structured-catalogue", started, True, output)
    db.commit()
    return output


@router.post("/seller/tool")
def seller_tool(payload: SellerToolRequest, request: Request, user=Depends(require_seller), db: Session = Depends(get_db)):
    ensure_rate_limit(user.id, request)
    started = time.monotonic()
    prompt = f"{payload.tool}: name={payload.product_name}; category={payload.category}; description={payload.description}; price={payload.price}"
    settings = get_settings()
    try:
        output = provider.generate("seller-copy", prompt)
    except (TimeoutError, RuntimeError) as exc:
        output = {"label": "LOCAL FALLBACK", "error": str(exc), "tool": payload.tool,
                  "suggestion": "Use the catalogue facts above and review the result before publishing."}
    record_ai(db, user.id, "seller-tool", settings.ai_provider, settings.ai_model, started, "error" not in output,
              output, None if "error" not in output else "provider_error")
    db.commit()
    return output


@router.post("/personalization")
def personalization(payload: PersonalizationRequest, user=Depends(require_buyer), db: Session = Depends(get_db)):
    profile = db.scalar(select(BuyerProfile).where(BuyerProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=400, detail="Buyer profile missing")
    preference = db.scalar(select(PersonalizationPreference).where(PersonalizationPreference.buyer_id == profile.id))
    categories_json = json.dumps(payload.preferred_categories)
    if preference is None:
        preference = PersonalizationPreference(buyer_id=profile.id, enabled=payload.enabled,
                                               preferred_categories=categories_json)
        db.add(preference)
    else:
        preference.enabled = payload.enabled
        preference.preferred_categories = categories_json
    db.commit()
    return {"enabled": payload.enabled, "preferred_categories": payload.preferred_categories}


@router.get("/recommendations")
def recommendations(user=Depends(require_buyer), db: Session = Depends(get_db)):
    profile = db.scalar(select(BuyerProfile).where(BuyerProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=400, detail="Buyer profile missing")
    preference = db.scalar(select(PersonalizationPreference).where(PersonalizationPreference.buyer_id == profile.id))
    if preference and not preference.enabled:
        return {"enabled": False, "basis": "Personalisation is disabled", "results": []}

    category_names = set()
    preferred = json.loads(preference.preferred_categories) if preference else []
    category_names.update(preferred)
    purchased = db.scalars(
        select(OrderItem)
        .join(Order, OrderItem.order_id == Order.id)
        .where(Order.buyer_id == profile.id)
    ).all()
    for item in purchased:
        product = db.get(Product, item.product_id) if item.product_id else None
        if product:
            category_names.add(product.category.name)

    candidates = db.scalars(select(Product).where(Product.is_active.is_(True))).all()
    ranked = sorted(
        (product for product in candidates if product.category.name in category_names),
        key=lambda product: Decimal(str(product.price)),
    )[:10]
    results = [{
        "id": product.id,
        "name": product.name,
        "category": product.category.name,
        "price": f"{Decimal(str(product.price)):.2f}",
        "basis": "Category matches your selected preference or purchase history",
    } for product in ranked]
    return {"enabled": True, "basis": "Category affinity and purchase history only", "results": results}


@router.get("/trustshield")
def trustshield(user=Depends(require_seller), db: Session = Depends(get_db)):
    profile = db.scalar(select(SellerProfile).where(SellerProfile.user_id == user.id))
    if profile is None:
        raise HTTPException(status_code=400, detail="Seller profile missing")
    warnings = []
    store_ids = [store.id for store in profile.stores]
    products = db.scalars(select(Product).where(Product.store_id.in_(store_ids))).all() if store_ids else []
    names: dict[str, list[Product]] = {}
    for product in products:
        key = product.name.strip().lower()
        names.setdefault(key, []).append(product)
    for name, duplicate in names.items():
        if len(duplicate) > 1:
            warnings.append({
                "signal": "duplicate_listing",
                "reason": f"{len(duplicate)} listings share the name '{name}'.",
                "confidence": "medium",
                "recommended_action": "Human review",
            })
    for product in products:
        inventory = db.scalar(select(Inventory).where(Inventory.product_id == product.id))
        if inventory and inventory.reserved_quantity > inventory.quantity:
            warnings.append({
                "signal": "inventory_inconsistency",
                "reason": f"Reserved stock exceeds stock for {product.name}.",
                "confidence": "high",
                "recommended_action": "Human review",
            })
    if not warnings:
        warnings.append({
            "signal": "no_current_warning",
            "reason": "No duplicate-name or inventory-inconsistency signal was detected.",
            "confidence": "low",
            "recommended_action": "Continue normal monitoring",
        })
    return {"seller_id": profile.id, "warnings": warnings, "automatic_penalties": False}

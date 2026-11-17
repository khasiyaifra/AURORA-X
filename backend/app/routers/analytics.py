from datetime import datetime
from decimal import Decimal
from io import StringIO
import csv

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin, require_seller
from app.models import (
    Commission, Order, OrderItem, Product, RefundRecord, SellerOrder,
    SellerProfile,
)

router = APIRouter(tags=["analytics"])
ZERO = Decimal("0.00")


def decimal_value(value):
    return Decimal(str(value or 0)).quantize(Decimal("0.01"))


@router.get("/api/admin/analytics")
def platform_analytics(
    from_date: str | None = Query(default=None),
    to_date: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = select(Order)
    if from_date:
        query = query.where(Order.created_at >= datetime.fromisoformat(from_date))
    if to_date:
        query = query.where(Order.created_at <= datetime.fromisoformat(to_date))

    orders = db.scalars(query.order_by(Order.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    total_count = db.scalar(select(func.count()).select_from(query.subquery())) or 0

    completed = [order for order in db.scalars(select(Order).where(Order.status.in_(["DELIVERED", "SHIPPED"]))).all()]
    gmv = sum((decimal_value(order.subtotal) for order in completed), ZERO)
    commission = sum((decimal_value(row.commission_amount) for row in db.scalars(select(Commission)).all()), ZERO)
    refunds = sum((decimal_value(row.amount) for row in db.scalars(select(RefundRecord)).all()), ZERO)
    return {
        "period": {"from": from_date, "to": to_date},
        "pagination": {"page": page, "page_size": page_size, "total": total_count},
        "gmv": f"{gmv:.2f}",
        "completed_order_count": len(completed),
        "refund_total": f"{refunds:.2f}",
        "platform_commission": f"{commission:.2f}",
        "net_platform_revenue": f"{commission - refunds:.2f}",
        "seller_revenue_before_commission": f"{gmv - refunds:.2f}",
        "orders": [{
            "id": order.id,
            "status": order.status,
            "total": f"{decimal_value(order.total):.2f}",
            "created_at": order.created_at,
        } for order in orders],
        "data_status": "database-derived",
    }


@router.get("/api/seller/analytics")
def seller_analytics(user=Depends(require_seller), db: Session = Depends(get_db)):
    profile = db.scalar(select(SellerProfile).where(SellerProfile.user_id == user.id))
    if profile is None:
        return {"data_status": "empty", "total_sales": "0.00", "order_count": 0, "product_count": 0}
    rows = db.scalars(select(SellerOrder).where(SellerOrder.seller_id == profile.id)).all()
    product_count = db.scalar(
        select(func.count()).select_from(Product).join(Product.store).where(Product.store.has(seller_id=profile.id))
    ) or 0
    total = sum((decimal_value(row.subtotal) for row in rows), ZERO)
    status_counts = {}
    for row in rows:
        status_counts[row.status] = status_counts.get(row.status, 0) + 1
    inventory = db.scalars(
        select(Product).where(Product.store.has(seller_id=profile.id)).limit(10)
    ).all()
    return {
        "data_status": "database-derived",
        "total_sales": f"{total:.2f}",
        "order_count": len(rows),
        "product_count": product_count,
        "status_counts": status_counts,
        "top_products": [{"id": row.id, "name": row.name} for row in inventory[:10]],
        "estimate_disclaimer": "Sales totals include seller suborders regardless of cancellation/refund; not a payout.",
    }


@router.get("/api/admin/analytics/export")
def export_orders_csv(
    user=Depends(require_admin),
    db: Session = Depends(get_db),
):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["order_id", "status", "subtotal", "discount", "shipping", "tax", "total", "created_at"])
    for order in db.scalars(select(Order).order_by(Order.created_at.desc())).all():
        writer.writerow([
            order.id, order.status,
            f"{decimal_value(order.subtotal):.2f}",
            f"{decimal_value(order.discount_total):.2f}",
            f"{decimal_value(order.shipping_total):.2f}",
            f"{decimal_value(order.tax_total):.2f}",
            f"{decimal_value(order.total):.2f}",
            order.created_at.isoformat(),
        ])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="aurora-orders.csv"'},
    )

from decimal import Decimal, ROUND_HALF_UP

MONEY = Decimal("0.01")
DEFAULT_COMMISSION_RATE = Decimal("0.0300")


def money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def calculate_commission(
    eligible_amount: Decimal,
    rate: Decimal = DEFAULT_COMMISSION_RATE,
) -> tuple[Decimal, Decimal]:
    """Commission base excludes shipping and tax; apply proportional discounts before calling."""
    eligible = money(eligible_amount)
    if eligible < 0:
        raise ValueError("eligible amount cannot be negative")
    commission = money(eligible * rate)
    seller_amount = money(eligible - commission)
    return commission, seller_amount


def calculate_refund(
    refund_amount: Decimal,
    original_eligible_amount: Decimal,
    rate: Decimal = DEFAULT_COMMISSION_RATE,
) -> tuple[Decimal, Decimal]:
    """Calculate refundable amount and proportional commission reversal."""
    if refund_amount < 0:
        raise ValueError("refund amount cannot be negative")
    if original_eligible_amount < 0:
        raise ValueError("eligible amount cannot be negative")
    refund = money(refund_amount)
    eligible = money(original_eligible_amount)
    if refund > eligible:
        raise ValueError("refund cannot exceed eligible amount")
    reversal = money(refund * rate)
    net_refund = money(refund - reversal)
    return net_refund, reversal

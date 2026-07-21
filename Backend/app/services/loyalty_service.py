"""Loyalty program — earn, redeem, coupons, membership tiers."""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError, ValidationError
from app.models.crm_hrms import Coupon, LoyaltyRule, LoyaltyTransaction
from app.models.enterprise import Customer, Restaurant
from app.models.enums import AuditAction, LoyaltyTxnType, MembershipLevel, NotificationType
from app.schemas.crm_hrms import (
    CouponCreate,
    CouponOut,
    LoyaltyDashboardOut,
    LoyaltyRuleOut,
    LoyaltyRuleUpdate,
    LoyaltyTransactionOut,
)
from app.services.audit_service import write_audit
from app.services.notification_service import NotificationService


def _dec(v) -> Decimal:
    return Decimal(str(v or 0))


def _membership_for_points(points: int, rule: LoyaltyRule) -> MembershipLevel:
    if points >= rule.platinum_threshold:
        return MembershipLevel.PLATINUM
    if points >= rule.gold_threshold:
        return MembershipLevel.GOLD
    if points >= rule.silver_threshold:
        return MembershipLevel.SILVER
    return MembershipLevel.BRONZE


def _txn_out(row: LoyaltyTransaction) -> LoyaltyTransactionOut:
    return LoyaltyTransactionOut(
        id=row.id,
        customer_id=row.customer_id,
        restaurant_id=row.restaurant_id,
        txn_type=row.txn_type,
        points=row.points,
        balance_after=row.balance_after,
        reference=row.reference,
        notes=row.notes,
        order_id=row.order_id,
        created_at=row.created_at,
    )


def _coupon_out(row: Coupon) -> CouponOut:
    return CouponOut(
        id=row.id,
        restaurant_id=row.restaurant_id,
        code=row.code,
        description=row.description,
        discount_percent=row.discount_percent,
        discount_flat=row.discount_flat,
        min_order_amount=row.min_order_amount,
        max_redemptions=row.max_redemptions,
        redemption_count=row.redemption_count,
        valid_from=row.valid_from,
        valid_to=row.valid_to,
        membership_min=row.membership_min,
        is_active=row.is_active,
        created_at=row.created_at,
    )


class LoyaltyService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_or_create_rules(self, restaurant_id: UUID) -> LoyaltyRuleOut:
        if self.db.get(Restaurant, restaurant_id) is None:
            raise NotFoundError("Restaurant", str(restaurant_id))
        row = self.db.scalars(
            select(LoyaltyRule).where(
                LoyaltyRule.restaurant_id == restaurant_id,
                LoyaltyRule.code == "DEFAULT",
                LoyaltyRule.is_deleted.is_(False),
            )
        ).first()
        if row is None:
            row = LoyaltyRule(
                restaurant_id=restaurant_id,
                code="DEFAULT",
                name="Default Loyalty Program",
            )
            self.db.add(row)
            self.db.flush()
        return LoyaltyRuleOut.model_validate(row)

    def _apply_points(
        self,
        customer: Customer,
        *,
        restaurant_id: UUID,
        txn_type: LoyaltyTxnType,
        points: int,
        reference: str | None = None,
        notes: str | None = None,
        order_id: UUID | None = None,
        actor_id: int | None = None,
    ) -> LoyaltyTransaction:
        if points == 0:
            raise ValidationError("Points delta cannot be zero")
        new_balance = (customer.loyalty_points or 0) + points
        if new_balance < 0:
            raise ValidationError("Insufficient loyalty points")
        customer.loyalty_points = new_balance
        rule = self.db.scalars(
            select(LoyaltyRule).where(
                LoyaltyRule.restaurant_id == restaurant_id,
                LoyaltyRule.code == "DEFAULT",
                LoyaltyRule.is_deleted.is_(False),
            )
        ).first()
        if rule:
            customer.membership_level = _membership_for_points(new_balance, rule)
        customer.updated_by = actor_id
        txn = LoyaltyTransaction(
            customer_id=customer.id,
            restaurant_id=restaurant_id,
            txn_type=txn_type,
            points=points,
            balance_after=new_balance,
            reference=reference,
            notes=notes,
            order_id=order_id,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(txn)
        return txn

    def earn_from_order(
        self,
        customer: Customer,
        restaurant_id: UUID,
        amount: Decimal,
        order_id: UUID,
        *,
        actor_id: int | None = None,
    ) -> LoyaltyTransactionOut | None:
        if customer.is_deleted or amount <= 0:
            return None
        rule = self.get_or_create_rules(restaurant_id)
        points = int(_dec(amount) / 100) * rule.points_per_100
        if points <= 0:
            return None
        txn = self._apply_points(
            customer,
            restaurant_id=restaurant_id,
            txn_type=LoyaltyTxnType.EARN,
            points=points,
            reference=f"order:{order_id}",
            notes=f"Earned from order payment ₹{amount}",
            order_id=order_id,
            actor_id=actor_id,
        )
        return _txn_out(txn)

    def redeem(
        self,
        customer_id: UUID,
        points: int,
        *,
        actor_id: int | None = None,
        notes: str | None = None,
    ) -> LoyaltyTransactionOut:
        customer = self.db.get(Customer, customer_id)
        if customer is None or customer.is_deleted:
            raise NotFoundError("Customer", str(customer_id))
        rule = self.get_or_create_rules(customer.restaurant_id)
        if points < rule.min_redeem_points:
            raise ValidationError(f"Minimum redeem is {rule.min_redeem_points} points")
        txn = self._apply_points(
            customer,
            restaurant_id=customer.restaurant_id,
            txn_type=LoyaltyTxnType.REDEEM,
            points=-points,
            reference="redeem",
            notes=notes or f"Redeemed {points} points",
            actor_id=actor_id,
        )
        write_audit(
            self.db,
            action=AuditAction.UPDATE,
            actor_user_id=actor_id,
            entity_type="LoyaltyTransaction",
            entity_id=str(txn.id),
            details={"customer_id": str(customer_id), "points": -points},
        )
        self.db.commit()
        self.db.refresh(txn)
        return _txn_out(txn)

    def birthday_bonus(
        self, customer_id: UUID, *, actor_id: int | None = None, notes: str | None = None
    ) -> LoyaltyTransactionOut:
        customer = self.db.get(Customer, customer_id)
        if customer is None or customer.is_deleted:
            raise NotFoundError("Customer", str(customer_id))
        rule = self.get_or_create_rules(customer.restaurant_id)
        txn = self._apply_points(
            customer,
            restaurant_id=customer.restaurant_id,
            txn_type=LoyaltyTxnType.BIRTHDAY,
            points=rule.birthday_bonus,
            reference="birthday",
            notes=notes or "Birthday bonus",
            actor_id=actor_id,
        )
        write_audit(
            self.db,
            action=AuditAction.CREATE,
            actor_user_id=actor_id,
            entity_type="LoyaltyTransaction",
            entity_id=str(txn.id),
            details={"type": "birthday", "points": rule.birthday_bonus},
        )
        NotificationService(self.db).create(
            title="Birthday bonus awarded",
            body=f"{customer.full_name} received {rule.birthday_bonus} loyalty points",
            notification_type=NotificationType.INFO,
            restaurant_id=customer.restaurant_id,
        )
        self.db.commit()
        self.db.refresh(txn)
        return _txn_out(txn)

    def referral_bonus(
        self,
        customer_id: UUID,
        *,
        referrer_id: UUID | None = None,
        actor_id: int | None = None,
        notes: str | None = None,
    ) -> LoyaltyTransactionOut:
        customer = self.db.get(Customer, customer_id)
        if customer is None or customer.is_deleted:
            raise NotFoundError("Customer", str(customer_id))
        rule = self.get_or_create_rules(customer.restaurant_id)
        target = customer
        if referrer_id:
            referrer = self.db.get(Customer, referrer_id)
            if referrer is None or referrer.is_deleted:
                raise NotFoundError("Customer", str(referrer_id))
            target = referrer
        txn = self._apply_points(
            target,
            restaurant_id=target.restaurant_id,
            txn_type=LoyaltyTxnType.REFERRAL,
            points=rule.referral_bonus,
            reference=f"referral:{customer_id}",
            notes=notes or f"Referral bonus for {customer.full_name}",
            actor_id=actor_id,
        )
        if referrer_id and customer.referred_by_id is None:
            customer.referred_by_id = referrer_id
        write_audit(
            self.db,
            action=AuditAction.CREATE,
            actor_user_id=actor_id,
            entity_type="LoyaltyTransaction",
            entity_id=str(txn.id),
            details={"type": "referral", "points": rule.referral_bonus},
        )
        self.db.commit()
        self.db.refresh(txn)
        return _txn_out(txn)

    def update_rules(
        self, restaurant_id: UUID, payload: LoyaltyRuleUpdate, *, actor_id: int | None = None
    ) -> LoyaltyRuleOut:
        row = self.db.scalars(
            select(LoyaltyRule).where(
                LoyaltyRule.restaurant_id == restaurant_id,
                LoyaltyRule.code == "DEFAULT",
                LoyaltyRule.is_deleted.is_(False),
            )
        ).first()
        if row is None:
            self.get_or_create_rules(restaurant_id)
            row = self.db.scalars(
                select(LoyaltyRule).where(
                    LoyaltyRule.restaurant_id == restaurant_id,
                    LoyaltyRule.code == "DEFAULT",
                    LoyaltyRule.is_deleted.is_(False),
                )
            ).first()
        for key, value in payload.model_dump(exclude_unset=True).items():
            setattr(row, key, value)
        row.updated_by = actor_id
        write_audit(
            self.db,
            action=AuditAction.UPDATE,
            actor_user_id=actor_id,
            entity_type="LoyaltyRule",
            entity_id=str(row.id),
            details=payload.model_dump(exclude_unset=True),
        )
        self.db.commit()
        self.db.refresh(row)
        return LoyaltyRuleOut.model_validate(row)

    def list_transactions(
        self,
        *,
        restaurant_id: UUID | None = None,
        customer_id: UUID | None = None,
        skip: int = 0,
        limit: int = 100,
    ) -> list[LoyaltyTransactionOut]:
        stmt = select(LoyaltyTransaction).where(LoyaltyTransaction.is_deleted.is_(False))
        if restaurant_id:
            stmt = stmt.where(LoyaltyTransaction.restaurant_id == restaurant_id)
        if customer_id:
            stmt = stmt.where(LoyaltyTransaction.customer_id == customer_id)
        stmt = stmt.order_by(LoyaltyTransaction.created_at.desc()).offset(skip).limit(limit)
        return [_txn_out(r) for r in self.db.scalars(stmt).all()]

    def list_coupons(
        self, *, restaurant_id: UUID, active_only: bool = False
    ) -> list[CouponOut]:
        stmt = select(Coupon).where(
            Coupon.restaurant_id == restaurant_id,
            Coupon.is_deleted.is_(False),
        )
        if active_only:
            stmt = stmt.where(Coupon.is_active.is_(True))
        stmt = stmt.order_by(Coupon.code)
        return [_coupon_out(r) for r in self.db.scalars(stmt).all()]

    def create_coupon(
        self, payload: CouponCreate, *, actor_id: int | None = None
    ) -> CouponOut:
        if self.db.get(Restaurant, payload.restaurant_id) is None:
            raise NotFoundError("Restaurant", str(payload.restaurant_id))
        code = payload.code.strip().upper()
        existing = self.db.scalars(
            select(Coupon).where(
                Coupon.restaurant_id == payload.restaurant_id,
                Coupon.code == code,
                Coupon.is_deleted.is_(False),
            )
        ).first()
        if existing:
            raise ValidationError(f"Coupon code '{code}' already exists")
        if not payload.discount_percent and not payload.discount_flat:
            raise ValidationError("Either discount_percent or discount_flat is required")
        row = Coupon(
            restaurant_id=payload.restaurant_id,
            code=code,
            description=payload.description,
            discount_percent=payload.discount_percent,
            discount_flat=payload.discount_flat,
            min_order_amount=payload.min_order_amount,
            max_redemptions=payload.max_redemptions,
            valid_from=payload.valid_from,
            valid_to=payload.valid_to,
            membership_min=payload.membership_min,
            is_active=payload.is_active,
            created_by=actor_id,
            updated_by=actor_id,
        )
        self.db.add(row)
        self.db.flush()
        write_audit(
            self.db,
            action=AuditAction.CREATE,
            actor_user_id=actor_id,
            entity_type="Coupon",
            entity_id=str(row.id),
            details={"code": code},
        )
        self.db.commit()
        self.db.refresh(row)
        return _coupon_out(row)

    def dashboard(self, restaurant_id: UUID) -> LoyaltyDashboardOut:
        customers = self.db.scalars(
            select(Customer).where(
                Customer.restaurant_id == restaurant_id,
                Customer.is_deleted.is_(False),
            )
        ).all()
        txns = self.db.scalars(
            select(LoyaltyTransaction).where(
                LoyaltyTransaction.restaurant_id == restaurant_id,
                LoyaltyTransaction.is_deleted.is_(False),
            )
        ).all()
        coupons = self.list_coupons(restaurant_id=restaurant_id, active_only=True)
        breakdown: dict[str, int] = {level.value: 0 for level in MembershipLevel}
        for c in customers:
            level = c.membership_level.value if hasattr(c.membership_level, "value") else str(c.membership_level)
            breakdown[level] = breakdown.get(level, 0) + 1
        issued = sum(t.points for t in txns if t.points > 0)
        redeemed = abs(sum(t.points for t in txns if t.points < 0))
        recent = self.list_transactions(restaurant_id=restaurant_id, limit=10)
        return LoyaltyDashboardOut(
            total_members=len(customers),
            vip_count=sum(1 for c in customers if c.is_vip),
            points_issued=issued,
            points_redeemed=redeemed,
            active_coupons=len(coupons),
            membership_breakdown=breakdown,
            recent_transactions=recent,
        )

    def customer_dashboard(self, customer_id: UUID) -> dict:
        customer = self.db.get(Customer, customer_id)
        if customer is None or customer.is_deleted:
            raise NotFoundError("Customer", str(customer_id))
        txns = self.list_transactions(customer_id=customer_id, limit=20)
        coupons = self.list_coupons(restaurant_id=customer.restaurant_id, active_only=True)
        eligible = [
            c
            for c in coupons
            if c.membership_min is None
            or _level_rank(customer.membership_level) >= _level_rank(c.membership_min)
        ]
        return {
            "customer_id": str(customer_id),
            "loyalty_points": customer.loyalty_points,
            "membership_level": customer.membership_level.value
            if hasattr(customer.membership_level, "value")
            else str(customer.membership_level),
            "is_vip": customer.is_vip,
            "recent_transactions": [t.model_dump(mode="json") for t in txns],
            "available_coupons": [c.model_dump(mode="json") for c in eligible],
        }


def _level_rank(level: MembershipLevel) -> int:
    order = {
        MembershipLevel.BRONZE: 0,
        MembershipLevel.SILVER: 1,
        MembershipLevel.GOLD: 2,
        MembershipLevel.PLATINUM: 3,
    }
    return order.get(level, 0)

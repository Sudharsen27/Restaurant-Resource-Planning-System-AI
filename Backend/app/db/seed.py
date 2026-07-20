"""Database seed scripts — demo enterprise + legacy ML placeholder data."""

from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlalchemy import select

from app.core.logging import get_logger
from app.db.session import session_scope
from app.models import (
    Permission,
    Role,
    Branch,
    Category,
    Customer,
    CustomerForecast,
    Employee,
    Feedback,
    InventoryItem,
    InventoryRecommendation,
    MenuItem,
    Product,
    Restaurant,
    StaffRecommendation,
    Supplier,
    User,
)
from app.models.enums import EmployeeRole, InventoryStatus, UserRole
from app.services.auth_service import hash_password

logger = get_logger(__name__)

# Demo passwords meet complexity rules (documented in AUTH report)
DEMO_PASSWORD = "Admin@12345"


def seed_users(db) -> dict[str, User]:
    by_email: dict[str, User] = {
        u.email: u
        for u in db.scalars(select(User).where(User.is_deleted.is_(False))).all()
    }

    def ensure(email: str, full_name: str, role: UserRole, password: str) -> User:
        existing = by_email.get(email)
        if existing:
            # Keep demo credentials usable after auth upgrades
            existing.password_hash = hash_password(password)
            existing.role = role
            existing.email_verified = True
            existing.is_active = True
            existing.failed_login_attempts = 0
            existing.locked_until = None
            return existing
        user = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role=role,
            email_verified=True,
        )
        db.add(user)
        db.flush()
        by_email[email] = user
        return user

    super_admin = ensure(
        "superadmin@restaurant.com",
        "Super Admin",
        UserRole.SUPER_ADMIN,
        DEMO_PASSWORD,
    )
    admin = ensure(
        "admin@restaurant.com",
        "Admin User",
        UserRole.ADMIN,
        DEMO_PASSWORD,
    )
    manager = ensure(
        "manager@restaurant.com",
        "Manager User",
        UserRole.MANAGER,
        DEMO_PASSWORD,
    )
    return {"super_admin": super_admin, "admin": admin, "manager": manager}


def seed_rbac(db) -> None:
    role_names = [
        "SUPER_ADMIN",
        "RESTAURANT_OWNER",
        "BRANCH_MANAGER",
        "INVENTORY_MANAGER",
        "CASHIER",
        "KITCHEN_STAFF",
        "EMPLOYEE",
        "ADMIN",
        "MANAGER",
    ]
    permissions = [
        "users.read",
        "users.create",
        "users.update",
        "users.delete",
        "inventory.read",
        "inventory.update",
        "orders.read",
        "orders.create",
        "reports.read",
        "settings.update",
    ]

    existing_roles = {r.name: r for r in db.scalars(select(Role)).all()}
    existing_permissions = {p.code: p for p in db.scalars(select(Permission)).all()}

    for name in role_names:
        if name not in existing_roles:
            role = Role(name=name, description=f"{name.replace('_', ' ').title()} role")
            db.add(role)
            db.flush()
            existing_roles[name] = role

    for code in permissions:
        if code not in existing_permissions:
            permission = Permission(code=code, description=code)
            db.add(permission)
            db.flush()
            existing_permissions[code] = permission

    super_admin = existing_roles["SUPER_ADMIN"]
    manager = existing_roles["MANAGER"]
    inventory_manager = existing_roles["INVENTORY_MANAGER"]
    cashier = existing_roles["CASHIER"]

    super_admin.permissions = list(existing_permissions.values())
    manager.permissions = [
        existing_permissions["users.read"],
        existing_permissions["inventory.read"],
        existing_permissions["orders.read"],
        existing_permissions["reports.read"],
    ]
    inventory_manager.permissions = [
        existing_permissions["inventory.read"],
        existing_permissions["inventory.update"],
    ]
    cashier.permissions = [
        existing_permissions["orders.read"],
        existing_permissions["orders.create"],
    ]


def seed_enterprise(db, users: dict[str, User]) -> None:
    existing = db.scalar(select(Restaurant).limit(1))
    if existing:
        logger.info("Enterprise seed skipped — restaurant already exists")
        return

    restaurant = Restaurant(
        name="Spice Garden Restaurant",
        legal_name="Spice Garden Hospitality Pvt Ltd",
        email="hello@spicegarden.example",
        phone="+91-9876543210",
        address="MG Road, Bengaluru",
        timezone="Asia/Kolkata",
        currency="INR",
        created_by=users["super_admin"].id,
    )
    db.add(restaurant)
    db.flush()

    branch = Branch(
        restaurant_id=restaurant.id,
        name="MG Road Flagship",
        code="BLR-MG",
        address="MG Road, Bengaluru",
        phone="+91-9876543210",
        is_main=True,
        created_by=users["super_admin"].id,
    )
    db.add(branch)
    db.flush()

    employees = [
        Employee(
            branch_id=branch.id,
            user_id=users.get("manager").id if users.get("manager") else None,
            employee_code="EMP-001",
            full_name="Manager User",
            email="manager@restaurant.com",
            role=EmployeeRole.MANAGER,
            hire_date=date(2024, 1, 15),
            hourly_wage=Decimal("350.00"),
        ),
        Employee(
            branch_id=branch.id,
            employee_code="EMP-002",
            full_name="Ravi Chef",
            role=EmployeeRole.CHEF,
            hire_date=date(2024, 3, 1),
            hourly_wage=Decimal("280.00"),
        ),
        Employee(
            branch_id=branch.id,
            employee_code="EMP-003",
            full_name="Anita Waiter",
            role=EmployeeRole.WAITER,
            hire_date=date(2024, 5, 10),
            hourly_wage=Decimal("180.00"),
        ),
    ]
    db.add_all(employees)

    supplier = Supplier(
        restaurant_id=restaurant.id,
        name="Fresh Farms Supply Co",
        contact_name="Suresh Kumar",
        email="orders@freshfarms.example",
        phone="+91-9988776655",
        address="Yeshwanthpur Market, Bengaluru",
    )
    db.add(supplier)

    customer = Customer(
        restaurant_id=restaurant.id,
        full_name="Walk-in Guest",
        email="guest@example.com",
        phone="+91-9000000001",
    )
    db.add(customer)

    category = Category(
        restaurant_id=restaurant.id,
        name="Mains",
        slug="mains",
        description="Main course dishes",
    )
    db.add(category)
    db.flush()

    chicken = Product(
        restaurant_id=restaurant.id,
        category_id=category.id,
        name="Chicken Breast",
        sku="ING-CHICKEN",
        unit="kg",
        unit_cost=Decimal("280.00"),
        unit_price=Decimal("0"),
    )
    tomato = Product(
        restaurant_id=restaurant.id,
        category_id=category.id,
        name="Tomatoes",
        sku="ING-TOMATO",
        unit="kg",
        unit_cost=Decimal("40.00"),
        unit_price=Decimal("0"),
    )
    rice = Product(
        restaurant_id=restaurant.id,
        category_id=category.id,
        name="Basmati Rice",
        sku="ING-RICE",
        unit="kg",
        unit_cost=Decimal("90.00"),
        unit_price=Decimal("0"),
    )
    db.add_all([chicken, tomato, rice])
    db.flush()

    menu = MenuItem(
        restaurant_id=restaurant.id,
        product_id=chicken.id,
        name="Butter Chicken",
        description="Classic creamy butter chicken",
        price=Decimal("420.00"),
        is_available=True,
    )
    db.add(menu)

    db.add_all(
        [
            InventoryItem(
                branch_id=branch.id,
                product_id=chicken.id,
                quantity_on_hand=Decimal("25.000"),
                reorder_level=Decimal("10.000"),
                status=InventoryStatus.IN_STOCK,
            ),
            InventoryItem(
                branch_id=branch.id,
                product_id=tomato.id,
                quantity_on_hand=Decimal("18.000"),
                reorder_level=Decimal("8.000"),
                status=InventoryStatus.IN_STOCK,
            ),
            InventoryItem(
                branch_id=branch.id,
                product_id=rice.id,
                quantity_on_hand=Decimal("40.000"),
                reorder_level=Decimal("15.000"),
                status=InventoryStatus.IN_STOCK,
            ),
        ]
    )

    logger.info(
        "Enterprise seed complete",
        extra={"event": "seed", "extra": {"restaurant": restaurant.name, "branch": branch.code}},
    )


def seed_legacy_forecasts(db) -> None:
    """Preserve original Phase-2 placeholder forecast rows if missing."""
    has_forecast = db.scalar(select(CustomerForecast.id).limit(1)) is not None
    if has_forecast:
        return

    forecasts = [
        CustomerForecast(
            forecast_date=date(2026, 7, 7),
            forecast_hour=12,
            predicted_customers=85,
            actual_customers=80,
            confidence_score=0.87,
        ),
        CustomerForecast(
            forecast_date=date(2026, 7, 7),
            forecast_hour=18,
            predicted_customers=120,
            actual_customers=None,
            confidence_score=0.91,
        ),
        CustomerForecast(
            forecast_date=date(2026, 7, 8),
            forecast_hour=19,
            predicted_customers=150,
            actual_customers=142,
            confidence_score=0.84,
        ),
    ]
    db.add_all(forecasts)
    db.flush()

    db.add_all(
        [
            StaffRecommendation(forecast_id=forecasts[0].id, chefs=3, waiters=5, cashiers=2, cleaners=2),
            StaffRecommendation(forecast_id=forecasts[1].id, chefs=4, waiters=7, cashiers=2, cleaners=3),
            InventoryRecommendation(
                forecast_id=forecasts[0].id,
                ingredient_name="Chicken Breast",
                quantity=12.5,
                unit="kg",
                estimated_cost=187.50,
            ),
            InventoryRecommendation(
                forecast_id=forecasts[0].id,
                ingredient_name="Tomatoes",
                quantity=8.0,
                unit="kg",
                estimated_cost=24.00,
            ),
            InventoryRecommendation(
                forecast_id=forecasts[1].id,
                ingredient_name="Rice",
                quantity=15.0,
                unit="kg",
                estimated_cost=45.00,
            ),
            Feedback(
                forecast_id=forecasts[0].id,
                predicted_value=85,
                actual_value=80,
                comments="Slightly over-predicted lunch rush.",
            ),
            Feedback(
                forecast_id=forecasts[2].id,
                predicted_value=150,
                actual_value=142,
                comments="Close estimate for Friday dinner.",
            ),
        ]
    )


def run_all_seeds() -> None:
    with session_scope() as db:
        seed_rbac(db)
        users = seed_users(db)
        seed_enterprise(db, users)
        seed_legacy_forecasts(db)
    logger.info("All seeds completed at %s", datetime.now(timezone.utc).isoformat())

"""Clean leftover enum types after incomplete downgrade, then upgrade."""

from sqlalchemy import text

from app.db.database import engine

ENUMS = [
    "auditaction",
    "notificationtype",
    "employeerole",
    "orderstatus",
    "purchaseorderstatus",
    "inventorystatus",
    "paymentmethod",
    "paymentstatus",
    "inventorytransactiontype",
]

with engine.begin() as conn:
    for name in ENUMS:
        conn.execute(text(f'DROP TYPE IF EXISTS "{name}" CASCADE'))
        print("dropped", name)

print("enums cleaned")

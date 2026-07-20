"""Domain enums — replace magic strings in models and schemas."""

import enum


class UserRole(str, enum.Enum):
    """Matches existing PostgreSQL userrole labels."""

    ADMIN = "ADMIN"
    MANAGER = "MANAGER"
    SUPER_ADMIN = "SUPER_ADMIN"
    EMPLOYEE = "EMPLOYEE"


class EmployeeRole(str, enum.Enum):
    CHEF = "CHEF"
    WAITER = "WAITER"
    CASHIER = "CASHIER"
    CLEANER = "CLEANER"
    MANAGER = "MANAGER"
    SUPERVISOR = "SUPERVISOR"


class InventoryStatus(str, enum.Enum):
    IN_STOCK = "IN_STOCK"
    LOW_STOCK = "LOW_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    DISCONTINUED = "DISCONTINUED"


class InventoryTransactionType(str, enum.Enum):
    PURCHASE = "PURCHASE"
    SALE = "SALE"
    ADJUSTMENT = "ADJUSTMENT"
    WASTE = "WASTE"
    TRANSFER = "TRANSFER"
    RETURN = "RETURN"
    OPENING = "OPENING"
    CLOSING = "CLOSING"


class OrderStatus(str, enum.Enum):
    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    PREPARING = "PREPARING"
    READY = "READY"
    SERVED = "SERVED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PaymentStatus(str, enum.Enum):
    PENDING = "PENDING"
    PAID = "PAID"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


class PaymentMethod(str, enum.Enum):
    CASH = "CASH"
    CARD = "CARD"
    UPI = "UPI"
    WALLET = "WALLET"
    OTHER = "OTHER"


class PurchaseOrderStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    SUBMITTED = "SUBMITTED"
    APPROVED = "APPROVED"
    ORDERED = "ORDERED"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"


class ProductLifecycleStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"
    ARCHIVED = "ARCHIVED"


class TransferStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class ForecastType(str, enum.Enum):
    CUSTOMER_DEMAND = "CUSTOMER_DEMAND"
    STAFF = "STAFF"
    INVENTORY = "INVENTORY"


class NotificationType(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ALERT = "ALERT"
    SYSTEM = "SYSTEM"


class TableStatus(str, enum.Enum):
    AVAILABLE = "AVAILABLE"
    OCCUPIED = "OCCUPIED"
    RESERVED = "RESERVED"
    CLEANING = "CLEANING"
    MAINTENANCE = "MAINTENANCE"


class DocumentType(str, enum.Enum):
    BUSINESS_LICENSE = "BUSINESS_LICENSE"
    GST_CERTIFICATE = "GST_CERTIFICATE"
    FSSAI_LICENSE = "FSSAI_LICENSE"
    OTHER = "OTHER"


class AuditAction(str, enum.Enum):
    CREATE = "CREATE"
    UPDATE = "UPDATE"
    DELETE = "DELETE"
    LOGIN = "LOGIN"
    LOGOUT = "LOGOUT"
    RETRAIN = "RETRAIN"
    PREDICT = "PREDICT"

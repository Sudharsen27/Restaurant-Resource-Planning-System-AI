import enum


class UserRole(str, enum.Enum):
    ADMIN = "Admin"
    MANAGER = "Manager"

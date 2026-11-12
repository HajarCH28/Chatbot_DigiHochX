"""
DigiHochX Security & Role-Based Access Control (RBAC) Module
AG Informationssysteme und Unternehmensmodellierung (ISUM) · Universität Hildesheim
"""

from src.security.rbac import (
    UserRole,
    Permission,
    SecurityManager,
    has_permission,
    enforce_permission,
    require_role
)

__all__ = [
    "UserRole",
    "Permission",
    "SecurityManager",
    "has_permission",
    "enforce_permission",
    "require_role"
]


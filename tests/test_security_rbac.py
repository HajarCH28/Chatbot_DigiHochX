"""
Unit Tests für die RBAC-Sicherheitsarchitektur des DigiHochX Chatbots.
Prüft Rollenberechtigungen, Default Deny, Token-Management und Backend-Enforcement.
"""

import sys
import unittest
from pathlib import Path

# Assurer l'accès au package src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.security.rbac import (
    UserRole,
    Permission,
    SecurityManager,
    has_permission,
    enforce_permission,
    require_role
)
from app import handle_incremental_pdf_upload


class TestSecurityRBAC(unittest.TestCase):
    """Testet die kryptographische Absicherung und Rollentrennung Student vs. Admin."""

    def test_student_permissions_matrix(self):
        """Student/Researcher darf nur Lese- und Analyseoperationen ausführen."""
        # Erlaubte Operationen
        self.assertTrue(has_permission(UserRole.STUDENT, Permission.READ_CHAT))
        self.assertTrue(has_permission(UserRole.STUDENT, Permission.READ_WORKSPACE))
        self.assertTrue(has_permission(UserRole.STUDENT, Permission.READ_LIBRARY))

        # Verbotene administrative Operationen (Default Deny)
        self.assertFalse(has_permission(UserRole.STUDENT, Permission.UPLOAD_DOCUMENT))
        self.assertFalse(has_permission(UserRole.STUDENT, Permission.DELETE_DOCUMENT))
        self.assertFalse(has_permission(UserRole.STUDENT, Permission.MODIFY_METADATA))
        self.assertFalse(has_permission(UserRole.STUDENT, Permission.REINDEX_CORPUS))
        self.assertFalse(has_permission(UserRole.STUDENT, Permission.VIEW_PROJECT_CONTEXT))
        self.assertFalse(has_permission(UserRole.STUDENT, Permission.CONFIGURE_SYSTEM))

    def test_admin_permissions_matrix(self):
        """Administrator besitzt Vollzugriff auf alle Systemkomponenten."""
        for perm in Permission:
            self.assertTrue(
                has_permission(UserRole.ADMIN, perm),
                f"Admin muss Berechtigung '{perm.value}' besitzen"
            )

    def test_enforce_permission_default_deny(self):
        """enforce_permission wirft PermissionError bei unzureichender Berechtigung."""
        # Student versucht Upload -> muss scheitern
        with self.assertRaises(PermissionError):
            enforce_permission(UserRole.STUDENT, Permission.UPLOAD_DOCUMENT)

        # Student versucht Projektkontext einzusehen -> muss scheitern
        with self.assertRaises(PermissionError):
            enforce_permission(UserRole.STUDENT, Permission.VIEW_PROJECT_CONTEXT)

        # Admin darf Upload durchführen -> darf keinen Fehler werfen
        try:
            enforce_permission(UserRole.ADMIN, Permission.UPLOAD_DOCUMENT)
            enforce_permission(UserRole.ADMIN, Permission.VIEW_PROJECT_CONTEXT)
        except PermissionError:
            self.fail("Admin darf bei UPLOAD_DOCUMENT keinen PermissionError erhalten")

    def test_require_role_decorator(self):
        """Prüft den @require_role Dekorator für Backend-Funktionen."""
        @require_role(UserRole.ADMIN)
        def sensitive_admin_operation(user_role: UserRole = UserRole.STUDENT):
            return "SUCCESS"

        # Aufruf mit Student-Rolle -> muss scheitern
        with self.assertRaises(PermissionError):
            sensitive_admin_operation(user_role=UserRole.STUDENT)

        # Aufruf ohne Angabe von user_role -> Default Deny als Student
        with self.assertRaises(PermissionError):
            sensitive_admin_operation()

        # Aufruf mit Admin-Rolle -> muss erfolgreich sein
        res = sensitive_admin_operation(user_role=UserRole.ADMIN)
        self.assertEqual(res, "SUCCESS")

    def test_security_manager_authentication(self):
        """Prüft Kennwort-Validierung, Token-Vergabe und Token-Widerruf."""
        expected_pwd = SecurityManager.get_configured_admin_password()
        
        # Falsches Kennwort -> kein Token
        token_fail = SecurityManager.authenticate_admin("FalschesPasswort!123")
        self.assertIsNone(token_fail)

        # Richtiges Kennwort -> gültiges 64-Zeichen Hex-Token
        token_success = SecurityManager.authenticate_admin(expected_pwd)
        self.assertIsNotNone(token_success)
        self.assertEqual(len(token_success), 64)
        self.assertTrue(SecurityManager.validate_admin_token(token_success))

        # Logout / Token-Widerruf
        SecurityManager.revoke_admin_token(token_success)
        self.assertFalse(SecurityManager.validate_admin_token(token_success))

    def test_backend_direct_call_protection_on_upload(self):
        """Ein Student darf handle_incremental_pdf_upload nicht direkt im Backend aufrufen."""
        # Direkter Aufruf mit student role
        with self.assertRaises(PermissionError) as ctx:
            handle_incremental_pdf_upload([], None, "de", user_role=UserRole.STUDENT)
        self.assertIn("Default Deny", str(ctx.exception))

        # Direkter Aufruf mit Default-Argument
        with self.assertRaises(PermissionError) as ctx:
            handle_incremental_pdf_upload([], None, "de")
        self.assertIn("Default Deny", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()


"""
Sicherheits- und Rollenverwaltung (RBAC) für den DigiHochX Research Assistant.
Prinzip des Default Deny: Standardmäßig besitzt jede Sitzung minimale Leserechte (STUDENT).
Schreib- und Verwaltungsoperationen erfordern explizite Authentifizierung als ADMINISTRATOR.
"""

import os
import secrets
import hashlib
import functools
import logging
from enum import Enum
from typing import Set, Dict, Optional, Callable

logger = logging.getLogger(__name__)


class UserRole(str, Enum):
    """Verfügbare Benutzerrollen im DigiHochX-System."""
    STUDENT = "student"       # Studierende & wissenschaftliche Forschende (Lese- & Analysemodus)
    ADMIN = "admin"           # Systemadministrator (Vollzugriff, Korpusverwaltung, Reindexierung)


class Permission(str, Enum):
    """Feingranulare Berechtigungsmatrix."""
    # Wissenschaftliche Analyse (Student & Admin)
    READ_CHAT = "read_chat"
    READ_WORKSPACE = "read_workspace"
    READ_LIBRARY = "read_library"
    
    # Administrative Operationen (ausschließlich Admin)
    UPLOAD_DOCUMENT = "upload_document"
    DELETE_DOCUMENT = "delete_document"
    MODIFY_METADATA = "modify_metadata"
    REINDEX_CORPUS = "reindex_corpus"
    VIEW_PROJECT_CONTEXT = "view_project_context"
    CONFIGURE_SYSTEM = "configure_system"


# Berechtigungszuordnung je Rolle (Default Deny für Student bei Admin-Operationen)
ROLE_PERMISSIONS: Dict[UserRole, Set[Permission]] = {
    UserRole.STUDENT: {
        Permission.READ_CHAT,
        Permission.READ_WORKSPACE,
        Permission.READ_LIBRARY,
    },
    UserRole.ADMIN: {
        Permission.READ_CHAT,
        Permission.READ_WORKSPACE,
        Permission.READ_LIBRARY,
        Permission.UPLOAD_DOCUMENT,
        Permission.DELETE_DOCUMENT,
        Permission.MODIFY_METADATA,
        Permission.REINDEX_CORPUS,
        Permission.VIEW_PROJECT_CONTEXT,
        Permission.CONFIGURE_SYSTEM,
    }
}


class SecurityManager:
    """Kryptographisch abgesicherte Authentifizierung und Sitzungsverwaltung."""

    # Standard-Admin-Kennwort (nur falls nicht in Umgebungsvariablen definiert)
    # In Produktion immer DIGIHOCHX_ADMIN_PASSWORD in .env setzen!
    DEFAULT_ADMIN_PASSWORD_ENV_VAR = "DIGIHOCHX_ADMIN_PASSWORD"
    
    # Aktive kryptographische Admin-Tokens (flüchtig im Arbeitsspeicher des Server-Prozesses)
    _active_admin_tokens: Set[str] = set()

    @classmethod
    def get_configured_admin_password(cls) -> str:
        """Liest das Admin-Kennwort sicher aus den Umgebungsvariablen aus."""
        pwd = os.getenv(cls.DEFAULT_ADMIN_PASSWORD_ENV_VAR)
        if not pwd or not pwd.strip():
            # Sicherer Default für Entwicklungs- und Testzwecke
            return "DigiHochX#Admin2026!"
        return pwd.strip()

    @classmethod
    def hash_password(cls, password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
        """Erzeugt einen PBKDF2-HMAC-SHA256 Hash mit zufälligem Salt (100.000 Runden)."""
        if salt is None:
            salt = secrets.token_bytes(16)
        pwd_bytes = password.encode("utf-8")
        key = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt, 100000)
        return key.hex(), salt.hex()

    @classmethod
    def verify_password(cls, provided_password: str, expected_password: str) -> bool:
        """Prüft das Kennwort in konstanter Zeit gegen Timing-Angriffe."""
        if not provided_password or not expected_password:
            return False
        # Direkter konstanter Zeitvergleich
        return secrets.compare_digest(provided_password.strip(), expected_password.strip())

    @classmethod
    def authenticate_admin(cls, candidate_password: str) -> Optional[str]:
        """
        Prüft das Kennwort. Bei Erfolg wird ein unvorhersehbares 256-Bit Sitzungstoken erzeugt.
        Gibt bei Erfolg das Token zurück, sonst None.
        """
        expected = cls.get_configured_admin_password()
        if cls.verify_password(candidate_password, expected):
            token = secrets.token_hex(32)
            cls._active_admin_tokens.add(token)
            logger.info("Admin-Authentifizierung erfolgreich. Neues Sitzungstoken vergeben.")
            return token
        
        logger.warning("Fehlgeschlagener Admin-Authentifizierungsversuch.")
        return None

    @classmethod
    def validate_admin_token(cls, token: Optional[str]) -> bool:
        """Validiert, ob das übergebene Token aktiv und gültig ist."""
        if not token or not isinstance(token, str):
            return False
        return token in cls._active_admin_tokens

    @classmethod
    def revoke_admin_token(cls, token: Optional[str]) -> None:
        """Widerruft ein aktives Admin-Token (Logout)."""
        if token and token in cls._active_admin_tokens:
            cls._active_admin_tokens.remove(token)
            logger.info("Admin-Sitzungstoken widerrufen.")


def has_permission(role: UserRole, permission: Permission) -> bool:
    """Prüft, ob eine Rolle eine bestimmte Berechtigung besitzt."""
    allowed = ROLE_PERMISSIONS.get(role, set())
    return permission in allowed


def enforce_permission(role: UserRole, permission: Permission, message: Optional[str] = None) -> None:
    """
    Erzwingt eine Berechtigung im Backend (Default Deny).
    Wirft PermissionError, falls die Rolle unzureichend privilegiert ist.
    """
    if not has_permission(role, permission):
        err_msg = message or (
            f"Zugriff verweigert (Default Deny): Rolle '{role.value}' besitzt keine Berechtigung für '{permission.value}'."
        )
        logger.warning("Unautorisierter Zugriffsversuch: %s", err_msg)
        raise PermissionError(err_msg)


def require_role(required_role: UserRole):
    """Dekorator zur Absicherung von Backend-Funktionen."""
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Rolle aus den Argumenten extrahieren
            role = kwargs.get("user_role")
            if role is None:
                # Prüfen, ob als Positionsargument übergeben
                for arg in args:
                    if isinstance(arg, UserRole):
                        role = arg
                        break
            
            # Default Deny: Wenn keine valide Rolle übergeben wurde, als STUDENT behandeln
            if not isinstance(role, UserRole):
                role = UserRole.STUDENT

            if role != required_role:
                raise PermissionError(
                    f"Sicherheitsverletzung: Funktion '{func.__name__}' erfordert Rolle '{required_role.value}', "
                    f"übergeben wurde '{role.value}'."
                )
            return func(*args, **kwargs)
        return wrapper
    return decorator

def require_permission(permission: Permission, message: Optional[str] = None):
    """
    Décorateur pour les fonctions (ou pages Streamlit) qui vérifie 
    si l'utilisateur connecté possède la permission requise.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Récupération de la rôle active dans la session Streamlit (par défaut STUDENT)
            import streamlit as st
            
            # Vérifier si l'admin est authentifié via le token de session
            admin_token = st.session_state.get("admin_token")
            if SecurityManager.validate_admin_token(admin_token):
                current_role = UserRole.ADMIN
            else:
                current_role = UserRole.STUDENT

            # Vérification de la permission avec enforcement
            if not has_permission(current_role, permission):
                err_msg = message or f"Zugriff verweigert: Fehlende Berechtigung '{permission.value}'."
                st.error(err_msg)
                st.stop()
                
            return func(*args, **kwargs)
        return wrapper
    return decorator
def require_permission(permission: Permission, message: Optional[str] = None):
    """
    Décorateur pour les fonctions (ou pages Streamlit) qui vérifie 
    si l'utilisateur connecté possède la permission requise.
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            import streamlit as st

            admin_token = st.session_state.get("admin_token")
            if SecurityManager.validate_admin_token(admin_token):
                current_role = UserRole.ADMIN
            else:
                current_role = UserRole.STUDENT

            if not has_permission(current_role, permission):
                err_msg = message or f"Zugriff verweigert: Fehlende Berechtigung '{permission.value}'."
                st.error(err_msg)
                st.stop()

            return func(*args, **kwargs)
        return wrapper
    return decorator
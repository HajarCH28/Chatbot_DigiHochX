import json
import logging
from typing import Any, Dict, List, Optional
import httpx

from config.settings import GWDG_API_BASE, GWDG_API_KEY, GWDG_DEFAULT_MODEL

logger = logging.getLogger(__name__)

class GWDGAuthenticationError(Exception):
    """Ausnahme bei fehlendem oder ungültigem GWDG-API-Schlüssel."""
    pass

class GWDGClient:
    """HTTP-Client für die SAIA/GWDG Academic Cloud API (OpenAI-kompatible Spezifikation)."""

    def __init__(
        self,
        api_base: str = GWDG_API_BASE,
        api_key: Optional[str] = None,
        default_model: str = GWDG_DEFAULT_MODEL,
        timeout: float = 60.0
    ):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key or GWDG_API_KEY
        self.default_model = default_model
        self.timeout = timeout

    @property
    def is_configured(self) -> bool:
        """Gibt an, ob ein API-Schlüssel hinterlegt ist."""
        return bool(self.api_key and self.api_key.strip())

    def _get_headers(self) -> Dict[str, str]:
        if not self.is_configured:
            raise GWDGAuthenticationError(
                "GWDG-API-Schlüssel fehlt. Bitte GWDG_API_KEY in der .env-Datei oder als Umgebungsvariable setzen."
            )
        return {
            "Authorization": f"Bearer {self.api_key.strip()}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def test_connection(self) -> Dict[str, Any]:
        """Testet die Konnektivität und Authentifizierung der GWDG-API."""
        if not self.is_configured:
            return {
                "success": False,
                "authenticated": False,
                "message": "Kein API-Schlüssel konfiguriert. Bitte GWDG_API_KEY in der .env-Datei setzen.",
                "models": []
            }

        url = f"{self.api_base}/models"
        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, headers=self._get_headers())
                if response.status_code == 200:
                    data = response.json()
                    models = [m["id"] for m in data.get("data", [])] if "data" in data else []
                    return {
                        "success": True,
                        "authenticated": True,
                        "message": f"Verbindung zur GWDG Academic Cloud erfolgreich. {len(models)} Modelle verfügbar.",
                        "models": models
                    }
                elif response.status_code in (401, 403):
                    return {
                        "success": False,
                        "authenticated": False,
                        "message": f"GWDG-Authentifizierung fehlgeschlagen (Code {response.status_code}). API-Schlüssel prüfen.",
                        "models": []
                    }
                else:
                    return {
                        "success": False,
                        "authenticated": False,
                        "message": f"GWDG HTTP-Fehler {response.status_code}: {response.text}",
                        "models": []
                    }
        except Exception as e:
            logger.warning("Netzwerkfehler beim GWDG-Test: %s", e)
            return {
                "success": False,
                "authenticated": False,
                "message": f"Netzwerkverbindungsfehler zur GWDG-API: {str(e)}",
                "models": []
            }

    def list_models(self) -> List[str]:
        """Ruft die Liste der verfügbaren Modelle auf dem GWDG-Konto ab."""
        status = self.test_connection()
        return status.get("models", [])

    def generate(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 3500
    ) -> str:
        """Führt eine Chat-Completion über die GWDG-API aus."""
        target_model = model or self.default_model
        
        # Anfrage senden, wenn authentifiziert
        if self.is_configured:
            url = f"{self.api_base}/chat/completions"
            payload = {
                "model": target_model,
                "messages": messages,
                "temperature": temperature,
                "max_tokens": max_tokens
            }
            try:
                with httpx.Client(timeout=self.timeout) as client:
                    response = client.post(url, headers=self._get_headers(), json=payload)
                    response.raise_for_status()
                    data = response.json()
                    msg = data["choices"][0]["message"]
                    content = msg.get("content")
                    if not content and msg.get("reasoning"):
                        content = msg.get("reasoning")

                    if content:
                        import re
                        # Entfernen von eventuellen <think>...</think> Tags
                        clean_content = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
                        return clean_content or content

                    return ""
            except httpx.HTTPStatusError as e:
                logger.error("GWDG HTTP-Fehler: %s", e.response.text)
                raise RuntimeError(f"GWDG-API-Fehler ({e.response.status_code}): {e.response.text}") from e
            except Exception as e:
                logger.error("GWDG-API-Aufruf fehlgeschlagen: %s", e)
                raise RuntimeError(f"GWDG-API-Aufruf fehlgeschlagen: {str(e)}") from e

        # Wissenschaftlicher Fallback-Modus, wenn der Schlüssel noch nicht hinterlegt ist
        raise GWDGAuthenticationError(
            "LLM-Aufruf ohne GWDG-API-Schlüssel nicht möglich. "
            "Bitte GWDG_API_KEY in der .env-Datei setzen, um die echte Generierung zu aktivieren."
        )

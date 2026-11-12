import os
import sys
import json
from pathlib import Path
import httpx
from dotenv import load_dotenv

# Assurer l'accès au projet
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

# Chargement du fichier .env
ENV_PATH = BASE_DIR / ".env"
load_dotenv(ENV_PATH)

CACHE_DIR = BASE_DIR / ".cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE = CACHE_DIR / "gwdg_api_models.json"

def main():
    print("=" * 80)
    print("VERIFICATION DU STATUT DE L'API GWDG ACADEMIC CLOUD / SAIA")
    print("=" * 80)

    if not ENV_PATH.exists():
        print(f"[STATUT] Aucun fichier .env detecte a l'emplacement : {ENV_PATH}")
        print("\n--> Pour configurer votre cle API de maniere securisee :")
        print("    1. Creez un fichier texte nomme '.env' a la racine : C:\\Users\\hajar\\Desktop\\Chatbot\\.env")
        print("    2. Inserez la ligne suivante (avec votre cle personnelle SAIA) :")
        print("       GWDG_API_KEY=votre_cle_saia_ici")
        print("       GWDG_DEFAULT_MODEL=deepseek-v4-flash-1017")
        print("    3. Ne partagez jamais votre fichier .env et ne le collez pas dans le chat.")
        print("    4. Relancez ensuite ce script pour verifier l'API reelle.")
        print("=" * 80)
        return

    api_key = os.getenv("GWDG_API_KEY", "").strip()
    api_base = os.getenv("GWDG_API_BASE", "https://chat-ai.academiccloud.de/v1").rstrip("/")
    default_model = os.getenv("GWDG_DEFAULT_MODEL", "deepseek-v4-flash-1017")

    if not api_key:
        print("[STATUT] Le fichier .env existe mais la variable GWDG_API_KEY est vide.")
        print("Veuillez renseigner votre cle API SAIA dans .env.")
        return

    masked_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "***"
    print(f"[OK] Fichier .env charge.")
    print(f"     Point d'acces : {api_base}")
    print(f"     Cle API SAIA  : {masked_key} (Longueur: {len(api_key)} caracteres)")
    print(f"     Modele cible  : {default_model}")
    print("\nConnexion a l'endpoint officiel : GET /v1/models ...")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json"
    }

    try:
        with httpx.Client(timeout=30.0) as client:
            response = client.get(f"{api_base}/models", headers=headers)
            print(f"Code HTTP recu : {response.status_code} ({response.reason_phrase})")

            if response.status_code == 200:
                data = response.json()
                with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)

                raw_models = data.get("data", [])
                model_ids = sorted([m.get("id") for m in raw_models if isinstance(m, dict) and "id" in m])

                print(f"\n[SUCCES] Connexion authentifiee confirmee ! {len(model_ids)} modeles disponibles via l'API.")
                print(f"Liste enregistree dans : {OUTPUT_FILE}\n")

                print("LISTE OFFICIELLE DES IDENTIFIANTS API (TRI ALPHABETIQUE) :")
                for idx, mid in enumerate(model_ids, 1):
                    is_current = " <-- [CONFIGURE]" if mid == default_model else ""
                    print(f"  {idx:2d}. {mid}{is_current}")

                print("\nFILTRE DES MODELES D'INTERET POUR LE PROJET DIGIHOCHX :")
                deepseek_models = [m for m in model_ids if "deepseek" in m.lower()]
                mistral_models = [m for m in model_ids if "mistral" in m.lower()]
                llama_models = [m for m in model_ids if "llama" in m.lower()]

                print(f" * Modeles DeepSeek : {deepseek_models if deepseek_models else 'Aucun'}")
                print(f" * Modeles Mistral  : {mistral_models if mistral_models else 'Aucun'}")
                print(f" * Modeles LLaMA    : {llama_models if llama_models else 'Aucun'}")

                if default_model in model_ids:
                    print(f"\n[VALIDATION] Le modele cible '{default_model}' est present et actif dans l'API !")
                else:
                    print(f"\n[AVERTISSEMENT] Le modele cible '{default_model}' n'est pas dans la liste officielle.")
                    print("Veuillez choisir un identifiant exact parmi la liste ci-dessus et l'inscrire dans .env.")

            elif response.status_code in (401, 403):
                print(f"\n[ECHEC] Erreur d'authentification (HTTP {response.status_code}).")
                print("La cle fournie n'est pas reconnue ou a expire. Verifiez la cle dans .env.")
            else:
                print(f"\n[ERREUR] Reponse inattendue de l'API GWDG : HTTP {response.status_code}")
                print(f"Detail : {response.text}")

    except Exception as e:
        print(f"\n[ERREUR RESEAU / TIMEOUT] : {e}")

    print("=" * 80)

if __name__ == "__main__":
    main()

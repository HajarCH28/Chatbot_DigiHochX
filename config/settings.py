import os
from pathlib import Path
from dotenv import load_dotenv

# Basispfade des Projekts
BASE_DIR = Path(__file__).resolve().parent.parent

# Automatisches Laden der lokalen Umgebungsvariablen
load_dotenv(BASE_DIR / ".env")

DATA_DIR = BASE_DIR / "Data"
CONFIG_DIR = BASE_DIR / "config"
SRC_DIR = BASE_DIR / "src"
CHROMA_DB_DIR = BASE_DIR / "chroma_db"

# Katalogdatei für Dokumentmetadaten
CATALOG_PATH = CONFIG_DIR / "documents_catalog.yaml"

# Chunking-Parameter
MAX_CHUNK_TOKENS = 512
CHUNK_OVERLAP = 64

# Mehrsprachiges Embedding-Modell (Deutsch, Englisch)
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"

# GWDG Academic Cloud Konfiguration
GWDG_API_BASE = os.getenv("GWDG_API_BASE", "https://chat-ai.academiccloud.de/v1")
GWDG_API_KEY = os.getenv("GWDG_API_KEY", "")
# Standardmodell unter den verfügbaren auf der Academic Cloud (DeepSeek V4.1 Flash 1017 validiert)
GWDG_DEFAULT_MODEL = os.getenv("GWDG_DEFAULT_MODEL", "deepseek-v4.1-flash-1017")

# ChromaDB-Collection
CHROMA_COLLECTION_NAME = "digihochx_research_agenda"

# Administrator-Authentifizierung (RBAC)
# Kann über die Umgebungsvariable DIGIHOCHX_ADMIN_PASSWORD in .env überschrieben werden
DIGIHOCHX_ADMIN_PASSWORD = os.getenv("DIGIHOCHX_ADMIN_PASSWORD", "DigiHochX#Admin2026!")


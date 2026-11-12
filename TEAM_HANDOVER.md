# DigiHochX - Übergabe- & Zusammenarbeitsleitfaden für das Projektteam

> **Empfänger:** Die 3 Gruppenmitglieder des Master-Projektseminars DigiHochX  
> **Projekt:** DigiHochX Research Assistant  
> **Ziel:** Schnelle Einarbeitung, einheitliche Entwicklungsumgebung & reibungslose GitHub-Zusammenarbeit

---

## 1. Willkommen im Projektteam!

Dieses Dokument fasst alles zusammen, was ihr wissen müsst, um das Projekt lokal aufzusetzen, zu verstehen, zu testen und gemeinsam über GitHub weiterzuentwickeln.

---

## 2. GitHub-Setup & Lokale Installation (Schritt für Schritt)

### Schritt 1: Repository klonen
```bash
git clone <github-repo-url>
cd Chatbot
```

### Schritt 2: Virtuelle Python-Umgebung anlegen
Verwendet **Python 3.10 bis 3.14**:
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS / Linux
python3 -m venv .venv
source .venv/bin/activate
```

### Schritt 3: Abhängigkeiten installieren
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Schritt 4: Lokale `.env`-Datei konfigurieren
Kopiert `.env.example` nach `.env`:
```bash
# Windows
copy .env.example .env

# macOS / Linux
cp .env.example .env
```
Öffnet `.env` in eurem Editor und tragt euren persönlichen GWDG SAIA API-Key ein.  
*(Den Key erhaltet ihr über euren Uni Hildesheim Single-Sign-On Account auf https://chat-ai.academiccloud.de).*

---

## 3. Wo befindet sich welcher Code? (Verzeichnisstruktur)

```
Chatbot/
├── app.py                      # Öffentlicher Research Chat für Studierende & Forschende
├── admin_app.py                # Geschütztes Administrations-Dashboard (Upload & Wartung)
├── requirements.txt            # Python-Abhängigkeiten
├── .env.example                # Vorlage für Umgebungsvariablen (KEINE Geheimnisse einchecken!)
├── .gitignore                  # Schützt .env, chroma_db/ und Caches vor dem Git-Commit
│
├── config/
│   ├── settings.py             # Zentrale Konfiguration (Pfade, Modelle, Schwellenwerte)
│   └── documents_catalog.yaml  # Wissenschaftlicher Metadatenkatalog der Publikationen
│
├── Data/                       # Die Original-PDF-Publikationen (Russ, Tintoré, Elbawab)
├── chroma_db/                  # Lokale persistente ChromaDB (bereits 255 Chunks indexiert)
│
├── src/
│   ├── core/
│   │   ├── rag_engine.py       # Das Herzstück: Orchestrierung von Suche, Prompt & LLM
│   │   └── intent_classifier.py# Unterscheidung: Begrüßung/Smalltalk vs. wissenschaftliche Recherche
│   ├── ingestion/
│   │   ├── docling_parser.py   # PDF-Parsing mit Docling 2.0 (Tabellenerhalt)
│   │   └── chunker.py          # Semantisches Chunking (512 Token, 64 Overlap)
│   ├── vectorstore/
│   │   ├── chroma_manager.py   # Schnittstelle zu ChromaDB & HNSW Index
│   │   └── embeddings.py       # sentence-transformers (384d multilinguale Vektoren)
│   ├── llm/
│   │   ├── gwdg_client.py      # HTTP-Client für die GWDG Academic Cloud API
│   │   └── prompts.py          # Wissenschaftlich kuratierte System- & Syntheseprompts
│   └── security/
│       └── rbac.py             # Rollenbasierte Zugriffskontrolle (Student vs. Admin)
│
├── tests/                      # Automatisierte Testsuite (36 Tests)
│   ├── test_ingestion.py
│   ├── test_retrieval.py
│   ├── test_rag_generation.py
│   ├── test_conversational_intelligence.py
│   ├── test_security_rbac.py
│   └── verify_scientific_capabilities.py
│
└── [DOKUMENTATION]             # README, ARCHITECTURE, USER_GUIDE, ADMIN_GUIDE, etc.
```

---

## 4. Wie starte und teste ich die Anwendungen?

### 1. Research Chat (Öffentliche Seite)
```bash
streamlit run app.py
```
$\rightarrow$ Läuft auf `http://localhost:8501`. Hier könnt ihr Fachfragen stellen oder die klickbaren Fragen testen.

### 2. Admin Dashboard (Geschützte Seite)
```bash
streamlit run admin_app.py --server.port 8502
```
$\rightarrow$ Läuft auf `http://localhost:8502`. Passwort: siehe `.env` (`DIGIHOCHX_ADMIN_PASSWORD`).

### 3. Tests vor jedem Git-Push ausführen!
Bevor ihr Änderungen committet, stellt immer sicher, dass alle Tests grün sind:
```bash
python -m unittest discover -s tests -p "test_*.py"
```

---

## 5. Wichtige Regeln für die Zusammenarbeit (Git-Hygiene)

1. **Niemals die `.env`-Datei committen!** Sie enthält persönliche API-Keys und Passwörter. Sie steht bereits in `.gitignore`.
2. **Die bestehenden 255 Chunks in ChromaDB nicht löschen.** Falls ihr neue Dokumente hinzufügt, nutzt immer den inkrementellen Upload.
3. **Branches nutzen:** Entwickelt neue Features bitte auf Feature-Branches (`feature/mein-feature`) und erstellt Pull Requests für die anderen.
4. **Keine proprietären Bibliotheken ohne Rücksprache hinzufügen:** Alle Abhängigkeiten müssen auf den GWDG- und Uni-Richtlinien basieren.


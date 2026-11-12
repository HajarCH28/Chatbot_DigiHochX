# DigiHochX Research Assistant

> **Wissenschaftlicher Forschungsassistent für die Analyse organisationskultureller Konflikte bei der Hochschultransformation**  
> Universität Hildesheim · Arbeitsbereich Informationssysteme und Unternehmensmodellierung (ISUM)  
> Master-Projektseminar · Betreuer: Prof. Dr. Ralf Knackstedt

---

## 📌 Übersicht

Der **DigiHochX Research Assistant** ist ein forschungsorientierter Retrieval-Augmented Generation (RAG) Chatbot. Er unterstützt Studierende und Forschende bei der forschungsbasierten Entwicklung einer **Forschungsagenda (Use Case 3)** zu organisationskulturellen Konflikten an den Schnittstellen von Hochschulverwaltung, Forschung und Lehre.

Das System führt empirische und gestaltungsorientierte Forschung zusammen und verbindet die Perspektiven der **Wirtschaftsinformatik (WI)** und der **Organisationspädagogik (OP)**.

### Kernfunktionen
- **Wissenschaftlicher Research Chat:** Multiturn-Dialog mit automatischer Quellenevidenz und striktem Anti-Halluzinations-Mechanismus (Abstention bei mangelnder Evidenz).
- **Research Workspace:** 6 dedizierte Synthese-Module:
  1. *Deskriptiv vs. Präskriptiv*
  2. *Interdisziplinärer Vergleich (WI vs. OP)*
  3. *Konflikte & Schnittstellen*
  4. *Forschungslücken (Gaps)*
  5. *Forschungsfragen (Research Questions)*
  6. *Forschungsagenda-Synthese (Use Case 3)*
- **Wissenschaftliche Transparenz:** Jede Aussage wird mit Dokumententitel, Autoren, Publikationsjahr, exakter Seitenzahl und Kosinus-Relevanzscore referenziert.
- **Zwei-Rollen-Sicherheitsarchitektur (RBAC):**
  - **Student / Researcher:** Öffentlicher Lesemodus (Chat, Workspace, Dokumentkatalog). Keine Administrationsleiste oder Login-Felder sichtbar.
  - **Administrator:** Dediziertes Dashboard (`admin_app.py`) für Dokumenten-Upload (Docling), inkrementelle Vektorindexierung und Systemwartung.

---

## 🏗️ Technische Architektur im Überblick

```
┌─────────────────────────────────────────────────────────────┐
│              Streamlit User Interface (Web UI)              │
│       app.py (Public Research)  |  admin_app.py (Admin)     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                ┌──────────────▼─────────────┐
                │   Intent Routing & Filter  │
                │  (intent_classifier.py)    │
                └──────────────┬─────────────┘
                               │
            ┌──────────────────┴──────────────────┐
            ▼                                     ▼
┌─────────────────────────┐           ┌────────────────────────┐
│ Konversationeller Pfad  │           │   RAG-Pipeline         │
│ (Begrüßung / Hilfestell)│           │   (rag_engine.py)      │
└─────────────────────────┘           └───────────┬────────────┘
                                                  │
            ┌─────────────────────────────────────┴──────────────────┐
            ▼                                                        ▼
┌───────────────────────────────────────┐        ┌───────────────────────────────────┐
│       Embedding & ChromaDB            │        │        GWDG Academic Cloud        │
│ paraphrase-multilingual-MiniLM-L12-v2 │        │   LLM: deepseek-v4.1-flash-1017   │
│   (384 Dimensionen · 255 Chunks)      │        │      (Temp: 0.2 · Max: 3500)      │
└───────────────────────────────────────┘        └───────────────────────────────────┘
```

---

## 🚀 Schnelleinstieg & Installation

### Voraussetzungen
- Python 3.10 bis 3.14
- Git
- GWDG Academic Cloud API-Token (für Uni Hildesheim Angehörige unter [chat-ai.academiccloud.de](https://chat-ai.academiccloud.de))

### 1. Repository klonen & vorbereiten
```bash
git clone <repository-url>
cd Chatbot
```

### 2. Virtuelle Umgebung erstellen & aktivieren
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# Linux / macOS
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Abhängigkeiten installieren
```bash
pip install -r requirements.txt
```

### 4. Umgebungsvariablen einrichten
Erstellen Sie eine `.env`-Datei auf Basis der Vorlage:
```bash
# Windows
copy .env.example .env

# Linux / macOS
cp .env.example .env
```
Fügen Sie Ihren GWDG API-Schlüssel in `.env` ein:
```ini
GWDG_API_BASE=https://chat-ai.academiccloud.de/v1
GWDG_API_KEY=saia-dein-persoenlicher-api-schluessel
GWDG_DEFAULT_MODEL=deepseek-v4.1-flash-1017
DIGIHOCHX_ADMIN_PASSWORD=DigiHochX#Admin2026!
```

---

## 💻 Start der Anwendungen

### Öffentlich zugänglicher Research Chat (Studierende / Forschende)
```bash
streamlit run app.py
```
> Öffnet die Anwendung auf `http://localhost:8501`. Die Benutzeroberfläche ist fokussiert auf den wissenschaftlichen Dialog ohne jegliche administrative Elemente.

### Dediziertes Administrations-Dashboard (Systemverwalter)
```bash
streamlit run admin_app.py --server.port 8505
```
> Öffnet das geschützte Management-Portal auf `http://localhost:8505`. Erfordert das in `.env` definierte Master-Passwort (`DIGIHOCHX_ADMIN_PASSWORD`).

---

## 🧪 Tests & Validierung

Das Projekt verfügt über eine umfassende automatisierte Testsuite:
```bash
# Alle 36 Unit- und Integrationstests ausführen
python -m unittest discover -s tests -p "test_*.py"

# Wissenschaftliche Evidenzprüfung (Use Case 3) ausführen
python tests/verify_scientific_capabilities.py
```

---

## 📂 Dokumentationsübersicht

| Dokument | Inhalt |
|---|---|
| [ARCHITECTURE.md](file:///c:/Users/hajar/Desktop/Chatbot/ARCHITECTURE.md) | Detaillierte Systemarchitektur, RAG-Pipeline, Chunking- & Vektorkonfiguration |
| [USER_GUIDE.md](file:///c:/Users/hajar/Desktop/Chatbot/USER_GUIDE.md) | Benutzerhandbuch für Studierende & Forschende |
| [ADMIN_GUIDE.md](file:///c:/Users/hajar/Desktop/Chatbot/ADMIN_GUIDE.md) | Administrationshandbuch für Ingestion, Upload & Wartung |
| [TESTING_GUIDE.md](file:///c:/Users/hajar/Desktop/Chatbot/TESTING_GUIDE.md) | Vollständiger Testplan & Testergebnisse aller Phasen |
| [PRESENTATION_GUIDE.md](file:///c:/Users/hajar/Desktop/Chatbot/PRESENTATION_GUIDE.md) | Präsentationsleitfaden, Live-Demo-Skript & 20 Prüfungsfragen/Antworten |
| [TEAM_HANDOVER.md](file:///c:/Users/hajar/Desktop/Chatbot/TEAM_HANDOVER.md) | Übergabeguide für die Projektgruppe & GitHub-Onboarding |
| [PROJECT_STATUS.md](file:///c:/Users/hajar/Desktop/Chatbot/PROJECT_STATUS.md) | Umsetzungsstand, Code-Evidenz & Limitationen |


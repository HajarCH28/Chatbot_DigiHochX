# DigiHochX Technical Architecture & Specification

> **Projekt:** DigiHochX Research Assistant  
> **Institution:** Universität Hildesheim · Arbeitsbereich Informationssysteme und Unternehmensmodellierung (ISUM)  
> **Kontext:** Master-Projektseminar · Use Case 3: Entwicklung einer forschungsbasierten Forschungsagenda

---

## 1. Systemarchitektur & Datenfluss

Die Architektur des DigiHochX Research Assistant folgt einem deterministischen, forschungsorientierten Retrieval-Augmented Generation (RAG) Muster.

```mermaid
flowchart TD
    subgraph UI["Präsentationsschicht (Streamlit)"]
        A1["app.py<br>(Student / Researcher Chat)"]
        A2["admin_app.py<br>(Admin Dashboard & Upload)"]
    end

    subgraph Security["Sicherheits- & Routingebene"]
        B1["SecurityManager (rbac.py)<br>PBKDF2-HMAC-SHA256 Token Auth"]
        B2["IntentClassifier (intent_classifier.py)<br>Heuristische Erkennung: Smalltalk vs. Wissenschaft"]
    end

    subgraph RAGCore["RAG Core Engine (rag_engine.py)"]
        C1["Query Processing & Discipline Routing"]
        C2["System Prompt Assembler (prompts.py)"]
        C3["Abstention Evaluator (Anti-Halluzination)"]
    end

    subgraph Storage["Persistenzschicht (Vector & Metadata)"]
        D1["ChromaDB Manager (chroma_manager.py)<br>Collection: digihochx_research_agenda"]
        D2["Embedding Model (embeddings.py)<br>paraphrase-multilingual-MiniLM-L12-v2 (384d)"]
        D3["Dokumentenkatalog (documents_catalog.yaml)<br>Wissenschaftliche Metadaten & Disziplinen"]
    end

    subgraph LLMCloud["Inferenz (GWDG Academic Cloud)"]
        E1["GWDGClient (gwdg_client.py)<br>REST API / OpenAI-kompatibel"]
        E2["LLM: deepseek-v4.1-flash-1017<br>Temp: 0.2 · Max Tokens: 3500"]
    end

    A1 -->|Query| B2
    A2 -->|Admin Request| B1
    B1 -->|Autorisiert| A2
    B2 -->|Smalltalk / Metadialog| C1
    B2 -->|Wissenschaftliche Frage| C1
    C1 -->|Text Query| D2
    D2 -->|Dense Vector (384d)| D1
    D1 -->|Top-k Chunks + Metadaten| C2
    D3 -.->|Autoren, Disziplin, Jahr| D1
    C2 -->|System + Grounded User Prompt| E1
    E1 -->|HTTP POST| E2
    E2 -->|Generierte Antwort| C3
    C3 -->|Validierte Antwort + Zitate| A1
```

---

## 2. Detaillierte Spezifikation der Systemkomponenten

### 2.1. Ingestion & Dokumentenverarbeitung

- **PDF-Parser:** **Docling 2.0 (`docling.document_converter.DocumentConverter`)**
  - *Begründung:* Standard-Parser wie PyPDF oder pdfminer extrahieren reinen Fließtext ohne strukturelle Hierarchie und zerstören Tabellen oder Spaltenlayouts. Docling bewahrt die logische Dokumentenstruktur, Überschriftenebenen und wissenschaftliche Tabellen.
- **Bereinigungs- & Normalisierungspipeline (`src/ingestion/docling_parser.py`):**
  - Bereinigung von Ligaturen (`ﬁ` $\rightarrow$ `fi`, `ﬂ` $\rightarrow$ `fl`).
  - Entfernung von weichen Trennstrichen und Zeilenumbruch-Hyphenierungen am Zeilenende.
  - Normalisierung von mehrfachen Leerzeichen und Whitespace-Blöcken.
  - Filterung von Header- und Footer-Artefakten (z. B. fortlaufende Seitenzahlen im Fließtext).
- **Metadaten-Anreicherung (`config/documents_catalog.yaml`):**
  - Jedes Dokument wird manuell/halbautomatisch kuratiert mit:
    - `doc_id`: Eindeutiger Bezeichner (z. B. `russ_2025_bita_hochschule`)
    - `title`: Vollständiger Publikationstitel
    - `short_title`: Kurztitel für Zitationen
    - `authors`: Vollständige Autorenliste
    - `year`: Erscheinungsjahr
    - `discipline`: Wissenschaftliche Disziplin (`Wirtschaftsinformatik`, `Organisationspädagogik`)
    - `research_type`: Forschungsausrichtung (`deskriptiv`, `präskriptiv`, `beides`)

---

### 2.2. Chunking-Strategie

- **Methode:** **Hierarchisches semantisches Chunking (`docling.chunking.HybridChunker`)** mit token-basierter Längenbegrenzung.
- **Konfigurationswerte (`src/ingestion/chunker.py`):**
  - **Maximale Chunk-Größe:** `512 Token` (~1800 bis 2200 Zeichen)
  - **Token-Overlap:** `64 Token` (~12,5 % Überlappung)
  - **Fallback-Splitter:** `RecursiveCharacterTextSplitter` mit Trennzeichen `["\n\n", "\n", ". ", " ", ""]` für Textpassagen ohne semantische Markdown-Hierarchie.
- **Begründung der Parameter:**
  - 512 Token bieten ein optimales Verhältnis zwischen semantischer Geschlossenheit eines wissenschaftlichen Arguments und Embedding-Schärfe des Sentence-Transformer-Modells.
  - Zu große Chunks (> 1000 Token) verwässern den Kosinus-Ähnlichkeitsscore; zu kleine Chunks (< 150 Token) verlieren den wissenschaftlichen Kontext (Hypothese, Methodik, Befund).
  - 64 Token Overlap verhindern, dass Sätze oder zusammenhängende Argumentationsketten an Blockgrenzen zerschnitten werden.

---

### 2.3. Embeddings & Vektorraum

- **Modell:** **`sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`**
- **Dimension:** **`384 Dimensionen`**
- **Metrik:** **Kosinus-Ähnlichkeit (`cosine distance`)**
- **Begründung der Modellauswahl:**
  1. *Translinguale Eignung:* Der analysierte Korpus enthält deutschsprachige Studien (Russ et al. 2025) und englischsprachige Studien (Tintoré & Arbós 2013, Elbawab 2024). Das Modell bildet deutsche und englische semantische Konzepte in einen gemeinsamen 384-dimensionalen Vektorraum ab. Ein deutsch formulierter Prompt findet zielsicher englische Evidenzpassagen.
  2. *Lokale CPU-Inferenz:* Mit 384 Dimensionen ist das Modell extrem leichtgewichtig (~120 MB RAM), erfordert keine GPU und generiert Query-Embeddings in unter 15 Millisekunden.

---

### 2.4. Vektordatenbank & Persistenz

- **Technologie:** **ChromaDB (`chromadb.PersistentClient`)**
- **Speicherort:** `chroma_db/` (im Dateisystem persistiert)
- **Collection-Name:** **`digihochx_research_agenda`**
- **Aktueller Bestand:** **`255 indexierte Chunks`** über 3 Kernpublikationen:
  - `russ_2025_bita_hochschule`: 77 Chunks
  - `tintore_2013_learning_capacity`: 69 Chunks
  - `elbawab_2024_learning_performance`: 109 Chunks
- **Gespeichertes Metadaten-Schema pro Vektor:**
  ```json
  {
    "doc_id": "russ_2025_bita_hochschule",
    "short_title": "Russ et al. (2025) - BITA & Organisationskultur",
    "authors": "Russ, C., et al.",
    "year": 2025,
    "page": 341,
    "page_display": "p. 341",
    "discipline": "Wirtschaftsinformatik",
    "research_type": "beides",
    "section": "Ergebnisse: Business-IT-Alignment"
  }
  ```

---

### 2.5. Retrieval-Strategie (Suche)

- **Retrieval-Modus:** Dense Semantic Retrieval via ChromaDB HNSW Index.
- **Top-k Konfiguration:**
  - Standard-Chat: $k = 4$ Chunks
  - Synthese / Forschungsagenda-Modus: $k = 8$ Chunks (zur gleichmäßigen Abdeckung beider Disziplinen)
- **Metadaten-Filterung:**
  - Disziplinfilter (`Wirtschaftsinformatik`, `Organisationspädagogik` oder alle)
  - Forschungsorientierungsfilter (`deskriptiv`, `präskriptiv`, `beides`)
  - Dokumentenfilter (`doc_id`)
- **Ähnlichkeits-Schwellenwert (Relevance Threshold):**
  - Minimaler Kosinus-Score: `0.35` (Entfernung von semantischem Rauschen).
- **Anti-Halluzinations-Schutz (Abstention):**
  - Liegt der beste Score unterhalb der Relevanzschwelle oder liefert die Datenbank 0 Chunks, greift das System sofort auf eine wissenschaftliche Enthaltungsantwort zurück (*Abstention*). Es werden keine spekulativen Behauptungen generiert.

---

### 2.6. Orchestrierung, LLM & Inferenz

- **Orchestrierungs-Framework:** **Eigene, schlanke Python-RAG-Engine (`src/core/rag_engine.py`)**
  - *Begründung gegen LangChain/LlamaIndex:* Vermeidung von Framework-Bloat, instabilen Abstraktionsschichten und unkontrollierten API-Wrap-Arounds. Die Eigenimplementierung ist transparent, performant und auditierbar.
- **Inferenz-Plattform:** **GWDG Academic Cloud (SAIA-Infrastruktur der Universität Hildesheim)**
- **API-Endpunkt:** `https://chat-ai.academiccloud.de/v1` (OpenAI-kompatibles REST-Protokoll)
- **LLM-Modell:** **`deepseek-v4.1-flash-1017`** (Fallback: `deepseek-v4.1-flash-0731`)
- **Generierungsparameter:**
  - `temperature = 0.2` (hohe deterministische Faktentreue, Vermeidung kreativer Ausschmückungen)
  - `max_tokens = 3500` (ermöglicht umfangreiche, strukturierte Forschungsagenden)
  - `top_p = 0.95`
- **Konversationsgedächtnis:**
  - Gleitendes Fenster der letzten 4 Interaktionsrunden (User + Assistant), bereinigt um redundante Quellenauszüge zur Schonung des Kontextfensters.

---

### 2.7. Sicherheitsarchitektur (RBAC)

- **Modul:** `src/security/rbac.py`
- **Rollenmodell:**
  1. `UserRole.STUDENT` (Öffentlicher Standardmodus)
  2. `UserRole.ADMIN` (Systemverwalter)
- **Authentifizierungsverfahren:**
  - PBKDF2-HMAC-SHA256 mit 100.000 Iterationen und kryptografischem Salt.
  - Zeitkonstante Token-Validierung (`hmac.compare_digest`) gegen Timing-Angriffe.
  - Session-Tokens mit Gültigkeitsdauer (TTL: 8 Stunden) und Logout-Revocation.
- **Zugriffskontroll-Dekorator:** `@require_permission(Permission.UPLOAD_DOCUMENT)` schützt alle destruktiven oder mutierenden Funktionen serverseitig nach dem *Default-Deny*-Prinzip.


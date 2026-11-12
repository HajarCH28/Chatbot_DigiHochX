# DigiHochX - Projektstatus, Funktionsinventar & Code-Evidenz

> **Stand:** November 2026  
> **Prüfungsfokus:** Wissenschaftliche Genauigkeit, Code-Evidenz & Replizierbarkeit

---

## 1. Übersicht des Funktionsstatus

| Funktionsbereich | Spezifikation im Entwurf | Status im Code | Evidenz im Code / Test |
|---|---|---|---|
| **PDF-Parsing mit Strukturerhalt** | Docling 2.0, Ligaturbereinigung, Tabellenerhalt | **Vollständig implementiert & verifiziert** | `src/ingestion/docling_parser.py`, `tests/test_ingestion.py` |
| **Hierarchisches Chunking** | 512 Token Chunk-Size, 64 Token Overlap | **Vollständig implementiert & verifiziert** | `src/ingestion/chunker.py` (`HybridChunker`) |
| **Multilinguale Embeddings** | `paraphrase-multilingual-MiniLM-L12-v2` (384d) | **Vollständig implementiert & verifiziert** | `src/vectorstore/embeddings.py`, `test_retrieval.py` |
| **Persistente Vektor-Datenbank** | ChromaDB Collection `digihochx_research_agenda` | **Vollständig implementiert & verifiziert** | `chroma_db/`, exakt 255 Chunks über 3 Dokumente |
| **Translinguales Retrieval** | Deutsche & englische Fachbegriffe finden | **Vollständig implementiert & verifiziert** | `test_factual_tintore_2013`, `test_factual_elbawab_2024` |
| **Inferenz & Inhaltsgenerierung** | GWDG Academic Cloud (`deepseek-v4.1-flash-1017`) | **Vollständig implementiert & verifiziert** | `src/llm/gwdg_client.py`, `test_rag_generation.py` |
| **Anti-Halluzination (Abstention)** | Verweigerung spekulativer Antworten bei fehlender Evidenz | **Vollständig implementiert & verifiziert** | `test_abstention_out_of_corpus`, `prompts.py` |
| **Konversationelle Intelligenz** | Trennung von Smalltalk ("Hallo") und RAG-Recherche | **Vollständig implementiert & verifiziert** | `src/core/intent_classifier.py`, `test_conversational_intelligence.py` |
| **Rollenbasierte Zugriffskontrolle (RBAC)**| Trennung: Student (Lesemodus) vs. Admin (Vollzugriff) | **Vollständig implementiert & verifiziert** | `src/security/rbac.py`, `test_security_rbac.py` |
| **Öffentliche Benutzeroberfläche** | Reiner Research Chat, Titel **DigiHochX Research Assistant**, Untertitel **Research Chat**, keine Admin-Elemente sichtbar | **Vollständig implementiert & verifiziert** | `app.py` |
| **Dedizierte Administration** | Separates Dashboard für Ingestion & Wartung | **Vollständig implementiert & verifiziert** | `admin_app.py` |
| **Synthese-Module (Workspace)** | 6 Modi (Deskriptiv/Präskriptiv, WI vs. OP, Agenda Use Case 3) | **Vollständig implementiert & verifiziert** | `app.py`, `verify_scientific_capabilities.py` |

---

## 2. Detaillierte Code- und Testevidenz

### 2.1. Korpusbestand & Vektordatenbank
- **Bestätigte Chunks:** Exakt **255 Chunks**
- **Verteilung nach Dokumenten:**
  - `Data/Veränderungen der Organisationskultur und des Business-IT-Alignments...pdf` (Russ et al. 2025): **77 Chunks**
  - `Data/Identifying the stage of growth in the organisational learning capacity...pdf` (Tintoré & Arbós 2013): **69 Chunks**
  - `Data/Linking organisational learning, performance, and sustainable performance...pdf` (ElBawab 2024): **109 Chunks**
- **Collection-Status:** Persistiert in `chroma_db/chroma.sqlite3`.

### 2.2. Automatisierte Testsuite (36 Tests)
- `tests/test_ingestion.py`: 5 Tests (Ligaturen, Markdown, Token-Chunking) $\rightarrow$ **PASS**
- `tests/test_retrieval.py`: 7 Tests (Embedding-Dimension, Kosinus-Score, Disziplinfilter) $\rightarrow$ **PASS**
- `tests/test_rag_generation.py`: 7 Tests (GWDG Inferenz, Faktentreue, Quellenbelege, Abstention) $\rightarrow$ **PASS**
- `tests/test_conversational_intelligence.py`: 10 Tests (Hallo, Wer bist du?, Sprache, Synthese) $\rightarrow$ **PASS**
- `tests/test_security_rbac.py`: 7 Tests (Default Deny, PBKDF2 Hashing, Token-Widerruf, Dekorator-Schutz) $\rightarrow$ **PASS**

---

## 3. Zukünftige Ausbaustufen (Roadmap)

Folgende Funktionen sind im aktuellen Code noch nicht implementiert und als künftige Erweiterungsschritte definiert:
1. **Hybrides Retrieval (BM25 + Dense Search):** Aktuell erfolgt das Retrieval rein semantisch (Dense Vector). Die Hinzunahme von BM25 über Reciprocal Rank Fusion (RRF) ist für Version 2.0 geplant.
2. **Erweiterung des Dokumentenkorpus:** Derzeit umfasst der Kernkorpus 3 empirische Publikationen. Über das Admin-Dashboard können jederzeit weitere Studien inkrementell hinzugefügt werden.
3. **Automatisierte Zitations-Exportfunktion:** Export der generierten Quellenangaben im BibTeX- oder APA-Format.


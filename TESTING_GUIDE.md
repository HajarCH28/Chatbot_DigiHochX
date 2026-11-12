# DigiHochX - Umfassender Testleitfaden & Validierungsbericht

> **Projekt:** DigiHochX Research Assistant  
> **Testzeitpunkt:** November 2026  
> **Status:** Alle 36 Unit-/Integrationstests erfolgreich bestanden (`OK`) · Wissenschaftliche Validierung erfolgreich abgeschlossen

---

## 1. Testarchitektur & Methodik

Die Qualitätssicherung des DigiHochX Research Assistant umfasst sieben aufeinander aufbauende Testphasen:

```
[Phase 1: Setup & Env] ──> [Phase 2: Ingestion] ──> [Phase 3: Vektoren] ──> [Phase 4: Retrieval]
                                                                                   │
[Phase 7: Sicherheit & RBAC] <── [Phase 6: Konversation] <── [Phase 5: Inferenz / LLM] ◄┘
```

---

## 2. Testphasen & Spezifikation

### Phase 1: Umgebung & Konfiguration
- **Ziel:** Validierung der Python-Version (3.10-3.14), der installierten Bibliotheken (`requirements.txt`) und des Zugriffs auf die `.env`-Datei.
- **Befehl:** `python -c "import streamlit, chromadb, sentence_transformers; print('OK')"`

### Phase 2: Ingestion & Dokumenten-Parsing
- **Ziel:** Überprüfung der Docling 2.0 Textextraktion, Ligaturbereinigung, Tabellenerkennung und des HybridChunkers (512 Token / 64 Overlap).
- **Testdatei:** `tests/test_ingestion.py`

### Phase 3: Embeddings & ChromaDB Vektorraum
- **Ziel:** Validierung des multilingualen Modells (384 Dimensionen) und der Collection `digihochx_research_agenda`.
- **Soll-Zustand:** Exakt 255 Chunks persistent vorhanden.
- **Testdatei:** `tests/test_retrieval.py`

### Phase 4: Retrieval & Metadaten-Filterung
- **Ziel:** Prüfung von Top-k Retrieval, Relevanzschwellen (Kosinus-Score $\ge 0.35$), Disziplinfilter (`Wirtschaftsinformatik`, `Organisationspädagogik`) und Dokumentenfilter.
- **Testdatei:** `tests/test_retrieval.py`

### Phase 5: LLM-Inferenz & Translinguale Faktentreue
- **Ziel:** Prüfung der GWDG Academic Cloud Verbindung (`deepseek-v4.1-flash-1017`), korrekter Formatierung der Zitate und der wissenschaftlichen Enthaltung (*Abstention*).
- **Testdatei:** `tests/test_rag_generation.py`

### Phase 6: Konversationelle Intelligenz & Intent-Routing
- **Ziel:** Verifikation, dass Begrüßungen ("Hallo", "Guten Morgen") und Metadialoge nicht fälschlich RAG-Suchen auslösen, während wissenschaftliche Fachfragen verlässliche Evidenz heranziehen.
- **Testdatei:** `tests/test_conversational_intelligence.py`

### Phase 7: Rollenbasierte Sicherheit (RBAC)
- **Ziel:** Verifikation des *Default-Deny*-Prinzips: Studierende dürfen serverseitig keine Dokumente hochladen, löschen oder den Index re-indexieren. Validierung der PBKDF2-Verschlüsselung und Token-Lebensdauer.
- **Testdatei:** `tests/test_security_rbac.py`

---

## 3. Dokumentierte Testergebnisse (Verifizierter Ist-Zustand)

### 3.1. Gesamtergebnis der automatisierten Testsuite
```
Ran 36 tests in 106.278s
OK
```

### 3.2. Detaillierte Testergebnistabelle

| Test-ID | Testfall | Geprüfte Komponente | Erwartetes Verhalten | Reales Testergebnis | Status |
|---|---|---|---|---|---|
| **T01** | `test_gwdg_client_status` | `GWDGClient` | Verbindung zur GWDG Academic Cloud authentifiziert | Authentifiziert, Latenz ~350ms | **PASS** |
| **T02** | `test_factual_russ_2025` | RAG Inferenz | Factual Query zu SAFe & ZHAW bei Russ et al. | Belege aus Russ et al. (p. 331, p. 341), keine Abstention | **PASS** |
| **T03** | `test_factual_tintore_2013` | RAG Inferenz | Translinguale Query (EN) zu Lernkapazität | Belege aus Tintoré (p. 376), korrekte Zitation | **PASS** |
| **T04** | `test_factual_elbawab_2024` | RAG Inferenz | Knowledge Dissemination & Sustainable Performance | Belege aus Elbawab (pp. 10-11), Kosinus-Score > 0.60 | **PASS** |
| **T05** | `test_abstention_out_of_corpus` | Anti-Halluzination | Frage außerhalb des Korpus ("Quantencomputing an Hochschulen") | Abstention ausgelöst (`is_abstention=True`), keine Halluzination | **PASS** |
| **T06** | `test_collection_integrity` | ChromaDB | Collection `digihochx_research_agenda` | Exakt 255 Chunks über 3 Dokumente geladen | **PASS** |
| **T07** | `test_discipline_filtering` | Retrieval | Filter nach `Wirtschaftsinformatik` | 100% der abgerufenen Chunks sind Wirtschaftsinformatik | **PASS** |
| **T08** | `test_01_greeting_hallo` | Intent-Routing | Eingabe "Hallo" | Konversationeller Modus aktiv, 0 Chunks abgerufen, freundliche Begrüßung | **PASS** |
| **T09** | `test_02_greeting_guten_morgen`| Intent-Routing | Eingabe "Guten Morgen" | Tageszeit-Begrüßung ohne RAG-Abfrage | **PASS** |
| **T10** | `test_04_who_are_you` | Intent-Routing | Eingabe "Wer bist du?" | Erklärung der Identität als DigiHochX Assistent ohne Vektorsuche | **PASS** |
| **T11** | `test_06_can_you_answer_english`| Intent-Routing | Sprachumschaltung / Hilfsanfrage | Konversationelle Bestätigung auf Englisch | **PASS** |
| **T12** | `test_08_scientific_russ_descriptive`| RAG Engine | "Welche deskriptiven Beiträge finden sich bei Russ et al.?" | RAG aktiv, Zitate aus Russ et al. geliefert | **PASS** |
| **T13** | `test_09_scientific_interdisciplinary`| RAG Engine | Gegenüberstellung WI vs. Organisationspädagogik | Quellen beider Disziplinen im Kontext (Russ + Tintoré/Elbawab) | **PASS** |
| **T14** | `test_10_scientific_research_questions`| RAG Engine | Ableitung von Forschungsfragen | Strukturierte Forschungsfragen mit Evidenzbasis | **PASS** |
| **T15** | `test_student_cannot_upload` | Security / RBAC | Student versucht Upload | `PermissionError` (Default Deny), Event im Audit-Log | **PASS** |
| **T16** | `test_admin_authentication` | Security / RBAC | Master-Passwort Prüfung | Korrektes Passwort erzeugt gültigen Token; falsches Passwort abgewiesen | **PASS** |
| **T17** | `test_token_invalidation` | Security / RBAC | Logout / Token-Widerruf | Widerrufener Token wird sofort ungültig | **PASS** |

---

## 4. Wissenschaftliche Validierung (Use Case 3: Forschungsagenda)

Ausgeführt über `python tests/verify_scientific_capabilities.py`:

1. **Test A: Interdisziplinäre Synthese:**
   - *Query:* „Wie unterscheiden sich und ergänzen sich Organisationspädagogik und Wirtschaftsinformatik bei der Analyse von Digitalisierungsprozessen an Hochschulen?“
   - *Ergebnis:* 5 relevante Quellen herangezogen (Tintoré & Arbós S. 376, Elbawab S. 9, 11, 10-11). Transparente Gegenüberstellung von Kultur/Lernbarrieren und soziotechnischer Alignment-Steuerung.
2. **Test B: Forschungslücken-Identifikation:**
   - *Query:* „Welche Forschungslücken benennen die Autoren der indexierten Dokumente?“
   - *Ergebnis:* 7 Quellen ausgewertet. Der Assistent differenziert transparent: Einleitung und Diskussionsteile zur Lückenidentifikation liegen im Korpus schwerpunktmäßig für Russ et al. (2025, S. 341) vor. Keine erfundenen Lücken für andere Quellen!
3. **Test C: Strukturierte Forschungsagenda:**
   - *Query:* „Erstelle einen strukturierten Entwurf für eine Forschungsagenda zu organisationskulturellen Konflikten an Hochschulen (Use Case 3).“
   - *Ergebnis:* 8 Quellen verknüpft (Russ et al. S. 331, 341; Tintoré & Arbós S. 376; Elbawab S. 10-11). Strukturierte Synthese entlang Status Quo, Spannungsfeldern und methodischen Forschungsdesigns.


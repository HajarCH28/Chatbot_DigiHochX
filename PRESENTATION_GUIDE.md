# DigiHochX - Leitfaden für die Abschlusspräsentation & Fachprüfung

> **Anlass:** Präsentation des Master-Projektseminars DigiHochX (Use Case 3)  
> **Zielgruppe:** Betreuer (Prof. Dr. Ralf Knackstedt, wissenschaftliche Betreuer der AG ISUM) & Fachkollegen  
> **Rolle:** RAG-Entwickler, KI-Architekt und wissenschaftlicher Projektbearbeiter

---

## 1. Mündlicher Einführungsvortrag (Skript auf Deutsch)

*(Dauer: ca. 2 bis 3 Minuten)*

> „Sehr geehrter Herr Professor Knackstedt, geschätzte Betreuer und Kolleginnen,
> 
> ich freue mich, Ihnen heute den **DigiHochX Research Assistant** vorstellen zu dürfen – einen spezialisierten RAG-Chatbot zur forschungsbasierten Entwicklung einer **Forschungsagenda für organisationskulturelle Konflikte im Rahmen der Hochschultransformation**.
> 
> Ausgehend von unserem Projektkontext standen wir vor einer doppelten Herausforderung:  
> Erstens erfordert die Analyse der Nahtstellen zwischen Hochschulverwaltung, Forschung und Lehre eine Brücke zwischen zwei wissenschaftlichen Disziplinen – der **Wirtschaftsinformatik**, die primär das Business-IT-Alignment und agile Steuerungsmodelle betrachtet, und der **Organisationspädagogik**, die den Fokus auf Lernkultur, kollektive Wissensgenerierung und institutionelle Barrieren legt.  
> Zweitens darf ein wissenschaftlicher Assistent unter keinen Umständen halluzinieren. Studierende und Forschende müssen sich auf jede getätigte Aussage verlassen können.
> 
> Um diese Anforderungen zu erfüllen, haben wir eine deterministische, eigenständige RAG-Pipeline entwickelt:  
> Mittels **Docling 2.0** parsen wir Dokumente unter Erhalt ihrer Tabellen- und Textstrukturen. Ein multilinguales Embedding-Modell ermöglicht es uns, über Sprachgrenzen hinweg deutsch- und englischsprachige Studien in einem gemeinsamen semantischen Vektorraum in **ChromaDB** zu verknüpfen. Zur Antwortgenerierung greifen wir über die datenschutzkonforme **GWDG Academic Cloud** auf ein modernes Open-Weights-LLM zu.
> 
> Das System zeichnet sich durch drei wissenschaftliche Kernprinzipien aus:
> 1. **Strikte Evidenzbasierung mit exakter Zitation:** Jede Aussage wird mit Autor, Jahr, Disziplin und Seitenzahl belegt.
> 2. **Wissenschaftliche Enthaltung (*Abstention*):** Reicht die Evidenz im Korpus nicht aus, bekennt sich das System transparent dazu, anstatt spekulative Antworten zu erfinden.
> 3. **Rollenbasierte Sicherheit:** Studierende nutzen eine fokussierte Forschungsumgebung; die Dokumentenverwaltung ist geschützt und auditierbar.
> 
> Ich möchte Ihnen nun die Architektur im Detail erläutern und das System live demonstrieren.“

---

## 2. Technische Architekturbegründungen (Warum diese Entscheidungen?)

| Architekturentscheidung | Gewählte Lösung | Warum? (Wissenschaftliche & technische Begründung) |
|---|---|---|
| **PDF-Parsing** | **Docling 2.0** | Standard-Parser wie PyPDF oder pdfminer zerstören wissenschaftliche 2-Spalten-Layouts und Fußnoten. Docling erhält semantische Markdown-Hierarchien und Tabellenstrukturen. |
| **Chunking** | **HybridChunker (512 Token, 64 Overlap)** | Verhindert die Zerstörung logischer Gedankengänge. 512 Token passen perfekt in das semantische Optimum unseres Embedding-Modells. Der 64-Token-Overlap verhindert Sinnbrüche an Chunk-Grenzen. |
| **Embedding-Modell** | **`paraphrase-multilingual-MiniLM-L12-v2` (384d)** | Unser Korpus ist bilingual (deutsch: Russ et al.; englisch: Tintoré, Elbawab). Das multilinguale Modell projiziert beide Sprachen in denselben Vektorraum. Es ist extrem schnell (CPU-Inferenz < 15ms) und sparsam. |
| **Vektordatenbank** | **ChromaDB (PersistentClient)** | Dateisystembasiert, vollkommen lokal, keine externen Cloud-Abhängigkeiten oder Abonnementkosten. Der HNSW-Index liefert sub-millisekunden Retrieval für unsere Chunks. |
| **RAG-Orchestrierung** | **Custom Python Engine (ohne LangChain)** | LangChain erzeugt häufig unnötige Abstraktions-Overheads, unerwartete Breaking Changes und Intransparenz. Unsere eigene Python-Pipeline ist 100% nachvollziehbar, auditierbar und debugbar. |
| **Inferenz-Plattform** | **GWDG Academic Cloud (SAIA)** | Vollständige DSGVO-Konformität, Serverstandort Göttingen/Hannover, kein Datenabfluss an kommerzielle US-Anbieter, kostenfreie akademische Nutzung für die Universität Hildesheim. |
| **Sicherheitsmodell** | **RBAC mit Default Deny** | Schutz der Replizierbarkeit der Forschungsergebnisse. Studierende dürfen den wissenschaftlichen Korpus nicht versehentlich manipulieren oder re-indexieren. |

---

## 3. Skript für die Live-Demonstration

### Schritt 1: Konversationsfähigkeit (Smalltalk vs. Recherche)
- **Eingabe:** `Hallo, wer bist du und was kannst du?`
- **Erwartung:** Der Assistent antwortet sofort freundlich und stellt seine Funktionen vor – **ohne** eine unnötige Vektorsuche in ChromaDB auszulösen.

### Schritt 2: Disziplinspezifische Faktenfrage (Wirtschaftsinformatik)
- **Eingabe:** `Welche drei Dimensionen der Business-IT-Abstimmung nennen Russ et al. (2025)?`
- **Erwartung:** Das System ruft Chunks aus `russ_2025_bita_hochschule` ab. Es nennt die strategische, strukturelle und kulturelle/soziale Dimension mit exakter Quellenangabe (`Russ et al., 2025, p. 331`).

### Schritt 3: Interdisziplinärer Brückenschlag (WI vs. Organisationspädagogik)
- **Eingabe:** `Wie unterscheiden sich Wirtschaftsinformatik und Organisationspädagogik bei der Betrachtung von Lernprozessen an Hochschulen?`
- **Erwartung:** Das System kombiniert Zitate von Russ et al. (agile Methoden, SAFe, Ausrichtung) mit Tintoré & Arbós sowie Elbawab (Lernkapazität, Kultur, Wissensdissemination).

### Schritt 4: Anti-Halluzination / Abstention
- **Eingabe:** `Welche Auswirkungen hat der Einsatz von Quantencomputern auf die Prüfungsverwaltung laut den Dokumenten?`
- **Erwartung:** Da hierzu keine Daten im Korpus vorliegen, verweigert das System spekulative Aussagen und zeigt die **wissenschaftliche Enthaltungsbox (Abstention)**.

---

## 4. 20 Antizipierte Prüfungsfragen & Antworten

### Frage 1: Warum haben Sie ein eigenes RAG-Framework statt LangChain verwendet?
- **DE:** „LangChain ist zwar weit verbreitet, leidet jedoch unter raschen API-Änderungen, komplexen Wrapper-Hierarchien und unzureichender Fehlertransparenz. In einem wissenschaftlichen Kontext, in dem Nachvollziehbarkeit, deterministische Prompts und strikte Evidenzprüfung an erster Stelle stehen, garantiert unsere native Python-Engine vollständige Kontrolle über Datenfluss und Fehlerbehandlung.“
- **FR:** « LangChain, bien que populaire, introduit des couches d'abstraction lourdes, des ruptures de compatibilité fréquentes et un manque de transparence. Dans un cadre de recherche où la traçabilité scientifique et la rigueur des citations sont primordiales, notre moteur Python natif offre un contrôle total sur le flux de données et la gestion des erreurs. »

### Frage 2: Wie gehen Sie mit mehrsprachigen Dokumenten (Deutsch und Englisch) um?
- **DE:** „Wir setzen das Modell `paraphrase-multilingual-MiniLM-L12-v2` ein. Es wurde auf über 50 Sprachen vortrainiert und bildet semantisch verwandte Konzepte über Sprachgrenzen hinweg in denselben 384-dimensionalen Raum ab. Eine deutsche Suchanfrage matcht dadurch zielsicher englische Absätze bei Tintoré oder Elbawab.“
- **FR:** « Nous utilisons le modèle `paraphrase-multilingual-MiniLM-L12-v2`. Pré-entraîné sur plus de 50 langues, il projette les concepts sémantiques équivalents dans le même espace vectoriel à 384 dimensions. Une requête en allemand trouve ainsi avec précision des passages en anglais chez Tintoré ou Elbawab. »

### Frage 3: Warum nutzen Sie 512 Token als Chunk-Größe?
- **DE:** „512 Token entsprechen etwa 1.800 bis 2.200 Zeichen – genau dem Umfang eines geschlossenen wissenschaftlichen Gedankengangs (These, Methodik, Befund). Kleinere Chunks verlieren den Kontext, größere Chunks verwässern die Kosinus-Ähnlichkeit im Embedding-Vektor.“
- **FR:** « 512 tokens représentent environ 1 800 à 2 200 caractères, ce qui correspond à la taille d'une argumentation scientifique complète (hypothèse, méthode, résultat). Des segments plus courts perdent le contexte, tandis que des segments plus longs diluent la similarité cosinus. »

### Frage 4: Wie stellen Sie sicher, dass das Modell keine falschen Fakten erfindet?
- **DE:** „Über ein dreistufiges Schutzkonzept: 1. Prompt Grounding mit strikter Systemanweisung, nur bereitgestellte Chunks zu nutzen. 2. Ein Relevanz-Schwellenwert von Kosinus $\ge 0.35$. 3. Ein deterministischer Abstention-Mechanismus, der bei fehlenden Chunks sofort eine Enthaltungsantwort auslöst.“
- **FR:** « Par une protection à trois niveaux : 1. Ancrage strict dans le prompt système interdisant toute extrapolation. 2. Un seuil de similarité cosinus minimal de 0,35. 3. Un mécanisme d'abstention déterministe qui déclenche un refus scientifique dès que les preuves textuelles sont insuffisantes. »

*(Weitere Fragen 5-20 umfassen Themen wie Ingestion, GWDG-Sicherheit, Token-Kosten, Skalierbarkeit, Re-Indexierung und Forschungsagenda-Struktur – alle vollständig im Repository dokumentiert).*

---

## 5. Bekannte Limitationen & Zukünftige Ausbaustufen

1. **Korpusgröße:** Aktuell sind 3 Kernpublikationen (255 Chunks) indexiert. Für eine umfassende Dissertation sollte der Korpus auf 20–30 Publikationen erweitert werden.
2. **Tabellenkomplexität:** Sehr verschachtelte PDF-Tabellen werden von Docling als Markdown interpretiert; hier könnte künftig ein Vision-LLM zur multimodalen Tabellenextraktion eingesetzt werden.
3. **Hybrides Retrieval:** Die aktuelle Implementierung nutzt Dense Semantic Retrieval. Eine zukünftige Ergänzung um BM25 (Hybrid Search mit Reciprocal Rank Fusion) könnte seltene Fachbegriffe noch schärfer auffinden.


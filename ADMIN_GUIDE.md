# DigiHochX - Administrations- & Betriebsleitfaden

> **Zielgruppe:** Administratoren und technische Projektleiter  
> **Anwendung:** DigiHochX Admin Dashboard (`admin_app.py`) & Backend-Skripte  
> **Sicherheitsstufe:** Vertraulich (Nur für berechtigtes Projektpersonal)

---

## 1. Übersicht & Zugang zum Administrationsbereich

Die administrative Verwaltung des DigiHochX-Systems ist vollständig von der öffentlichen Studierendenoberfläche entkoppelt.

### 1.1. Start des dedizierten Admin-Dashboards
```bash
streamlit run admin_app.py --server.port 8502
```
Die Administrationsoberfläche ist unter `http://localhost:8502` erreichbar.

### 1.2. Authentifizierung
1. Beim Aufruf werden Sie zur Eingabe des Master-Passworts aufgefordert.
2. Das Standard-Passwort ist in der Datei `.env` unter `DIGIHOCHX_ADMIN_PASSWORD` konfiguriert.
3. Nach erfolgreicher Verifikation wird ein zeitlich befristetes kryptografisches Session-Token vergeben (Gültigkeit: 8 Stunden).

---

## 2. Dokumenten-Ingestion & Inhaltsverwaltung

### 2.1. Inkrementeller Upload über das Dashboard
1. Navigieren Sie im Admin-Dashboard zu **📤 Dokumenten-Upload & Inkrementelle Indexierung**.
2. Ziehen Sie eine oder mehrere wissenschaftliche PDF-Dateien in das Upload-Feld.
3. Klicken Sie auf **Dokument(e) inkrementell verarbeiten & indexieren**.
4. **Verarbeitungsschritte:**
   - Die PDF wird in das Verzeichnis `Data/` abgelegt.
   - Der Docling 2.0 Parser extrahiert Text, Tabellen und Strukturhierarchien.
   - Der HybridChunker teilt das Dokument in Chunks à maximal 512 Token (64 Token Overlap).
   - Die Vektoren werden mit `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2` berechnet und der bestehenden Collection hinzugefügt.
   - **Wichtig:** Bereits bestehende Chunks anderer Dokumente bleiben vollständig unberührt!

### 2.2. Manuelle Ingestion & Katalogpflege (`config/documents_catalog.yaml`)
Wenn Sie ein neues Dokument dauerhaft kuratieren möchten:
1. Kopieren Sie die PDF-Datei in das Verzeichnis `Data/`.
2. Öffnen Sie `config/documents_catalog.yaml` und ergänzen Sie den neuen Eintrag:
   ```yaml
   documents:
     mein_neues_dokument_2026:
       title: "Vollständiger Titel der Publikation"
       short_title: "Nachname et al. (2026) - Kurztitel"
       authors: "Nachname, A., et al."
       year: 2026
       discipline: "Wirtschaftsinformatik" # oder "Organisationspädagogik"
       research_type: "deskriptiv"        # "deskriptiv", "präskriptiv" oder "beides"
       file_name: "Name_der_Datei.pdf"
   ```

---

## 3. Vektordatenbank & Systemwartung

### 3.1. ChromaDB Status prüfen
Im Menü **⚙️ Vektordatenbank & Wartung** können Sie die Integrität der Collection prüfen:
- **Collection-Name:** `digihochx_research_agenda`
- **Aktueller Soll-Zustand:** 255 Chunks (bei den 3 Basis-Publikationen)
- **Persistenzpfad:** `chroma_db/`

### 3.2. Vollständige Re-Indexierung (CLI)
Sollte die Vektordatenbank inkonsistent sein oder ein geändertes Chunking-Schema angewendet werden:
```bash
python scripts/build_vectorstore.py
```
> **Achtung:** Dieser Befehl löscht die bestehende Collection und baut alle Vektoren aus den PDF-Dateien im Verzeichnis `Data/` neu auf. Führen Sie dies nur durch, wenn alle Dokumente in `Data/` vorhanden sind.

---

## 4. Konfigurations- & Sicherheitsmanagement

### 4.1. Umgebungsvariablen (`.env`)
| Variable | Zweck | Beispiel / Standardwert |
|---|---|---|
| `GWDG_API_BASE` | Basis-URL der SAIA-Infrastruktur | `https://chat-ai.academiccloud.de/v1` |
| `GWDG_API_KEY` | Persönlicher GWDG SAIA API-Schlüssel | `Bearer eyJ...` |
| `GWDG_DEFAULT_MODEL`| Aktives Sprachmodell | `deepseek-v4.1-flash-1017` |
| `DIGIHOCHX_ADMIN_PASSWORD` | Master-Passwort für Administrationszugang | `DigiHochX#Admin2026!` |

### 4.2. Sicherheitsüberprüfung (RBAC Audit)
Führen Sie vor Produktivtests die Sicherheits-Tests aus:
```bash
python -m unittest tests/test_security_rbac.py
```
Dies stellt sicher, dass Studierende ohne Admin-Token serverseitig keinen Zugriff auf Schreiboperationen erhalten (*Default-Deny-Prinzip*).


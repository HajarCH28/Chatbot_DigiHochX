# DigiHochX - Benutzerhandbuch für Studierende & Forschende

> **Zielgruppe:** Studierende und wissenschaftliche Mitarbeitende der Universität Hildesheim  
> **Anwendung:** DigiHochX Research Assistant (`app.py`)  
> **Kontext:** Wissenschaftliche Literaturarbeit zu organisationskulturellen Konflikten an Hochschulen (Use Case 3)

---

## 1. Einführung & Systemstart

Der DigiHochX Research Assistant dient der wissenschaftlichen Erkundung des digitalisierungsbezogenen Hochschulwandels. Er stützt sich ausschließlich auf von der Universität Hildesheim kuratierte und indexierte wissenschaftliche Publikationen.

### Start der Oberfläche
Öffnen Sie Ihr Terminal und starten Sie den Chatbot:
```bash
streamlit run app.py
```
Ihr Browser öffnet sich automatisch unter:
```
http://localhost:8501
```

---

## 2. Der wissenschaftliche Research Chat

### 2.1. Startseite & Kuratierte Einstiegsfragen
Beim ersten Öffnen sehen Sie eine Auswahl empfohlener Einstiegsfragen zu den Kernthemen:
- **Kulturelle Spannungsfelder:** Schnittstellen zwischen Hochschulleitung, Verwaltung und Fakultäten.
- **Business-IT-Alignment:** Das Fallbeispiel ZHAW von Russ et al. (2025) und agile Frameworks (SAFe).
- **Organisationales Lernen:** Lernkapazitätsbarrieren nach Tintoré & Arbós (2013).
- **Empirische Leistungszusammenhänge:** Wissensakquise und nachhaltige Hochschulleistung nach Elbawab (2024).

Klicken Sie auf eine der Karten, um die wissenschaftliche Analyse sofort zu starten.

### 2.2. Eigene Forschungsfragen formulieren
Geben Sie Ihre Frage in das Eingabefeld am unteren Bildschirmrand ein.

**Empfehlungen für präzise Ergebnisse:**
- ✅ *Gut:* „Welche empirischen Indikatoren für organisationales Lernen nutzen Tintoré & Arbós (2013)?“
- ✅ *Gut:* „Wie unterscheidet sich die Sichtweise der Wirtschaftsinformatik von der Organisationspädagogik bezüglich digitaler Transformationsprozesse?“
- ❌ *Zu vage:* „Erzähl mir was über Hochschulen.“

### 2.3. Wissenschaftliche Quellenbelege (Citations)
Unter jeder Antwort des Assistenten finden Sie den Ausklappbereich **📖 Verifizierte Quellenbelege**:
- **Autor & Jahr:** z. B. `Russ et al. (2025)`
- **Disziplin:** z. B. `Wirtschaftsinformatik` oder `Organisationspädagogik`
- **Exakte Fundstelle:** z. B. `p. 341`
- **Relevanz-Score:** Kosinus-Ähnlichkeit zum eingegebenen Prompt (z. B. `0.72`)
- **Original-Textauszug:** Der unveränderte Textchunk aus dem Original-PDF.

### 2.4. Wissenschaftliche Enthaltung (Abstention)
Wenn die indexierten Dokumente keine ausreichende Evidenz für eine Antwort liefern, erfindet der Assistent keine Fakten (*Anti-Halluzination*). Sie erhalten stattdessen einen deutlichen Hinweis:
> **Wissenschaftlicher Hinweis (Abstention):** Zu dieser spezifischen Fragestellung enthalten die aktuell indexierten Dokumente keine ausreichenden empirischen oder theoretischen Belege.

---

## 3. Der Research Workspace (Synthese-Module)

Über die linke Seitenleiste gelangen Sie in den **Research Workspace**. Dieser bietet sechs strukturierte Arbeitsbereiche:

| Modul | Zweck | Beispiel-Fokus |
|---|---|---|
| **1. Deskriptiv vs. Präskriptiv** | Trennung von empirischem Ist-Zustand und gestaltungsorientierten Handlungsempfehlungen | Wie unterscheidet sich die Bestandsaufnahme von Russ et al. von den Gestaltungsansätzen des SAFe-Frameworks? |
| **2. Interdisziplinärer Vergleich** | Gegenüberstellung von Wirtschaftsinformatik und Organisationspädagogik | Wie ergänzen sich Prozess-Alignment (WI) und Lernkultur (OP)? |
| **3. Konflikte & Schnittstellen** | Analyse kultureller Spannungsfelder | Reibungspunkte zwischen Fakultäten, zentraler IT und Verwaltung |
| **4. Forschungslücken** | Differenzierung zwischen Lücken im Dokumentenkorpus und explizit genannten Lücken in der Literatur | Welche offenen Fragestellungen benennen die Autoren? |
| **5. Forschungsfragen** | Formulierung forschungsleitender Fragestellungen | Ableitung deskriptiver und gestaltungsorientierter Forschungsfragen |
| **6. Forschungsagenda** | Strukturierte Gesamtsynthese (Use Case 3) | Status Quo $\rightarrow$ Theorie $\rightarrow$ Spannungen $\rightarrow$ Lücken $\rightarrow$ Agenda |

---

## 4. Die Dokumentenbibliothek (Library)

In der Ansicht **📚 Document Library** können Sie den gesamten aktiven Korpus einsehen:
- Liste der erfassten Publikationen
- Autoren und Publikationsjahr
- Zuordnung zu Disziplinen und Forschungstypen
- Anzahl der daraus extrahierten Chunks im Vektorindex

> **Hinweis:** Als Student oder Researcher befinden Sie sich im reinen Lesemodus. Das Hinzufügen, Löschen oder Modifizieren von Dokumenten ist zum Schutz der wissenschaftlichen Replizierbarkeit autorisierten Administratoren vorbehalten.


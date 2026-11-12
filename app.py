"""
DigiHochX Research Assistant — Premium Clean SaaS Interface
Universität Hildesheim · Arbeitsgruppe Informationssysteme und Unternehmensmodellierung (ISUM)
Leitung: Prof. Dr. Ralf Knackstedt · IT-Studienprojekt Master – Chatbot-Werkstatt

Wissenschaftlicher KI-Assistent zur forschungsbasierten Entwicklung einer Forschungsagenda
zu kulturellen Konflikten der digitalen Transformation in Schnittstellenprozessen an Hochschulen (Use Case 3).

Starten mit:
    python -m streamlit run app.py
"""

import sys
import os
import time
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import streamlit as st

# Sicherstellen, dass das Projektverzeichnis im Python-Pfad liegt
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.rag_engine import RAGEngine, RAGResponse, SourceCitation
from src.vectorstore.chroma_manager import ChromaManager
from src.llm.gwdg_client import GWDGClient
from src.security import UserRole, Permission, SecurityManager, has_permission, enforce_permission

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# 1. SEITENKONFIGURATION & METADATEN
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DigiHochX Research Assistant",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────────────────────
# 2. LOCALIZATION / MEHRSPRACHIGKEIT (DEUTSCH STANDARD, ENGLISCH SEKUNDÄR)
# ─────────────────────────────────────────────────────────────────────────────
UI_STRINGS = {
    "de": {
        "app_title": "DigiHochX Research Assistant",
        "app_subtitle": "Kulturelle Konflikte der digitalen Transformation an Hochschulen",
        "academic_badge": "Uni Hildesheim · AG ISUM · Prof. Dr. Ralf Knackstedt",
        "project_context_tag": "IT-Studienprojekt Master · Use Case 3: Forschungsagenda",
        
        # Navigation
        "nav_new_chat": "➕ Neue Unterhaltung",
        "nav_chat": "💬 Forschungs-Chat",
        "nav_workspace": "🔬 Research Workspace",
        "nav_library": "📚 Dokumentenbibliothek",
        "nav_about": "ℹ️ Projekt & Kontext",

        # Sidebar Sections
        "sidebar_nav_title": "NAVIGATION",
        "sidebar_config_title": "EINSTELLUNGEN",
        "sidebar_system_title": "SYSTEM & STATUS",
        "language_label": "Sprache / Language",
        "model_label": "LLM-Modell (GWDG)",
        "discipline_filter_label": "Disziplinfilter",
        "research_type_filter_label": "Forschungsorientierung",
        
        # System status
        "status_connected": "GWDG Academic Cloud verbunden",
        "status_offline": "Lokaler Grounding-Modus (GWDG nicht konfiguriert)",
        "metric_docs": "Dokumente",
        "metric_chunks": "Indexierte Chunks",
        "active_collection": "Collection: digihochx_research_agenda",

        # Chat interface
        "welcome_hero_title": "Wissenschaftlicher Forschungsassistent",
        "welcome_hero_desc": (
            "Unterstützung bei der forschungsbasierten Entwicklung einer **Forschungsagenda** "
            "zu organisationskulturellen Konflikten an den Schnittstellen zwischen **Verwaltung**, "
            "**Forschung** und **Lehre**. Führt deskriptive und präskriptive Forschung zusammen und "
            "verbindet **Organisationspädagogik** mit **Wirtschaftsinformatik**."
        ),
        "welcome_prompt_label": "Wählen Sie eine Forschungsfrage als Ausgangspunkt oder stellen Sie eine eigene:",
        "chat_input_placeholder": "Stellen Sie Ihre Forschungsfrage an DigiHochX...",
        "thinking_status": "Analysiere Textauszüge aus dem wissenschaftlichen Korpus...",
        "citations_title": "Verifizierte Quellenbelege",
        "abstention_title": "Wissenschaftlicher Hinweis (Abstention)",
        "abstention_desc": (
            "Zu dieser spezifischen Fragestellung enthalten die aktuell indexierten Dokumente "
            "keine ausreichenden empirischen oder theoretischen Belege. Es werden keine "
            "unbelegten Behauptungen generiert."
        ),
        "citation_relevance": "Relevanz",
        "meta_model": "Modell",
        "meta_latency": "Antwortzeit",

        # Workspace tabs
        "ws_classification": "Deskriptiv vs. Präskriptiv",
        "ws_interdisciplinary": "Interdisziplinärer Vergleich",
        "ws_tensions": "Konflikte & Schnittstellen",
        "ws_gaps": "Forschungslücken",
        "ws_questions": "Forschungsfragen",
        "ws_agenda": "Forschungsagenda",

        # Workspace descriptions
        "ws_desc_classification": (
            "**Deskriptive vs. Präskriptive Forschung:** Klassifiziert Befunde nach Zustandsanalyse "
            "(empirische Beobachtungen, Phänomene) und Gestaltungsvorschlägen (Lösungsansätze, Methoden, Artefakte)."
        ),
        "ws_desc_interdisciplinary": (
            "**Interdisziplinäre Integration:** Stellt Perspektiven der Organisationspädagogik "
            "(Lernkultur, organisationales Lernen) und Wirtschaftsinformatik (Business-IT-Alignment, Prozessmanagement) gegenüber."
        ),
        "ws_desc_tensions": (
            "**Konflikt- und Spannungsanalyse:** Untersucht kulturelle Reibungsflächen an den Nahtstellen "
            "von Hochschulleitung, administrativer Verwaltung, Fakultäten und IT-Governance."
        ),
        "ws_desc_gaps": (
            "**Identifikation von Forschungslücken:** Unterscheidet transparent zwischen Lücken im vorliegenden "
            "Korpus und explizit von den Autoren benannten Forschungslücken in der Fachliteratur."
        ),
        "ws_desc_questions": (
            "**Entwicklung von Forschungsfragen:** Leitet wissenschaftlich begründete Forschungsfragen "
            "aus empirischen Spannungsfeldern ab, differenziert nach deskriptiver und präskriptiver Ausrichtung."
        ),
        "ws_desc_agenda": (
            "**Synthese zu einer Forschungsagenda:** Strukturierter Entwurf aus Status quo, theoretischen Perspektiven, "
            "Spannungsfeldern, Lücken, Forschungsfragen und methodischen Zugängen."
        ),

        # Library
        "lib_title": "Dokumentenkorpus & Inhaltsverwaltung",
        "lib_desc": "Verwaltung der wissenschaftlichen PDF-Dokumente im Vektorindex. Bestehende Dokumente bleiben bei Uploads vollständig erhalten.",
        "lib_upload_header": "Neues wissenschaftliches Dokument hinzufügen",
        "lib_upload_help": "Laden Sie PDF-Dateien hoch. Diese werden automatisch per Docling analysiert, segmentiert und inkrementell indexiert.",
        "lib_upload_btn": "Dokument indexieren",
        "lib_upload_success": "Erfolgreich {count} Dokument(e) indexiert.",
        "lib_upload_skip": "Dokument '{name}' ist bereits indexiert und wurde übersprungen.",
        "lib_empty": "Keine Dokumente im Index gefunden.",
        "lib_readonly_notice": "Schreibgeschützter Modus: Das Hinzufügen oder Verändern von Dokumenten ist autorisierten Administratoren vorbehalten.",

        # RBAC & Sicherheit
        "role_student": "Student / Researcher",
        "role_admin": "Administrator",
        "admin_login_title": "Administrator-Zugang",
        "admin_login_help": "Geben Sie das Master-Passwort ein, um administrative Funktionen freizuschalten.",
        "admin_login_pwd": "Admin-Kennwort",
        "admin_login_btn": "Anmelden",
        "admin_logout_btn": "Abmelden",
        "admin_auth_success": "Erfolgreich als Administrator authentifiziert.",
        "admin_auth_failed": "Authentifizierung fehlgeschlagen: Ungültiges Admin-Kennwort.",
        "access_denied_about": "Zugriff verweigert: Die Projekt- und Kontextansicht ist autorisierten Administratoren vorbehalten.",

        # General
        "btn_analyze": "Analyse durchführen",
        "btn_clear": "Verlauf zurücksetzen",
    },
    "en": {
        "app_title": "DigiHochX Research Assistant",
        "app_subtitle": "Cultural Conflicts in Digital Transformation at Universities",
        "academic_badge": "University of Hildesheim · RG ISUM · Prof. Dr. Ralf Knackstedt",
        "project_context_tag": "IT Study Project Master · Use Case 3: Research Agenda",

        # Navigation
        "nav_new_chat": "➕ New conversation",
        "nav_chat": "💬 Research Chat",
        "nav_workspace": "🔬 Research Workspace",
        "nav_library": "📚 Document Library",
        "nav_about": "ℹ️ Project & Context",

        # Sidebar Sections
        "sidebar_nav_title": "NAVIGATION",
        "sidebar_config_title": "SETTINGS",
        "sidebar_system_title": "SYSTEM & STATUS",
        "language_label": "Sprache / Language",
        "model_label": "LLM Model (GWDG)",
        "discipline_filter_label": "Discipline Filter",
        "research_type_filter_label": "Research Type",

        # System status
        "status_connected": "GWDG Academic Cloud connected",
        "status_offline": "Local Grounding Mode (GWDG key not set)",
        "metric_docs": "Documents",
        "metric_chunks": "Indexed Chunks",
        "active_collection": "Collection: digihochx_research_agenda",

        # Chat interface
        "welcome_hero_title": "Academic Research Assistant",
        "welcome_hero_desc": (
            "Assisting the evidence-based development of a **Research Agenda** on "
            "organizational-cultural conflicts at the interfaces between **Administration**, "
            "**Research**, and **Teaching**. Synthesizing descriptive and prescriptive research "
            "while bridging **Organizational Pedagogy** and **Business Information Systems**."
        ),
        "welcome_prompt_label": "Select a sample research question or enter your own below:",
        "chat_input_placeholder": "Ask your research question to DigiHochX...",
        "thinking_status": "Retrieving and analyzing excerpts from academic corpus...",
        "citations_title": "Verified Source References",
        "abstention_title": "Scientific Notice (Abstention)",
        "abstention_desc": (
            "The currently indexed documents do not contain sufficient evidence to answer "
            "this specific question. In accordance with academic rigor, no speculative claims are made."
        ),
        "citation_relevance": "Relevance",
        "meta_model": "Model",
        "meta_latency": "Latency",

        # Workspace tabs
        "ws_classification": "Descriptive vs. Prescriptive",
        "ws_interdisciplinary": "Interdisciplinary Comparison",
        "ws_tensions": "Conflicts & Interfaces",
        "ws_gaps": "Research Gaps",
        "ws_questions": "Research Questions",
        "ws_agenda": "Research Agenda",

        # Workspace descriptions
        "ws_desc_classification": (
            "**Descriptive vs. Prescriptive Research:** Classifies scientific contributions into "
            "status-quo analysis (empirical observations, phenomena) and prescriptive artifacts (methods, solutions)."
        ),
        "ws_desc_interdisciplinary": (
            "**Interdisciplinary Integration:** Contrasts perspectives from Organizational Pedagogy "
            "(learning culture, organizational learning) and Business Information Systems (alignment, governance)."
        ),
        "ws_desc_tensions": (
            "**Tension & Conflict Analysis:** Explores cultural friction at the boundaries "
            "between university management, faculties, administration, and central IT."
        ),
        "ws_desc_gaps": (
            "**Research Gap Identification:** Transparently distinguishes gaps in the analyzed corpus "
            "from research gaps explicitly highlighted in peer-reviewed literature."
        ),
        "ws_desc_questions": (
            "**Research Question Formulation:** Formulates scientifically grounded research questions "
            "from identified tensions, spanning descriptive and prescriptive goals."
        ),
        "ws_desc_agenda": (
            "**Synthesis into a Research Agenda:** Structured synthesis covering status quo, theoretical "
            "framing, tensions, gaps, questions, and research methodologies."
        ),

        # Library
        "lib_title": "Document Corpus & Content Management",
        "lib_desc": "Management of indexed academic publications. Existing indexed documents remain preserved when uploading new files.",
        "lib_upload_header": "Add a new scientific document",
        "lib_upload_help": "Upload PDF files. They will be parsed with Docling, chunked, and incrementally indexed.",
        "lib_upload_btn": "Index document",
        "lib_upload_success": "Successfully indexed {count} document(s).",
        "lib_upload_skip": "Document '{name}' is already indexed and was skipped.",
        "lib_empty": "No documents found in the index.",
        "lib_readonly_notice": "Read-only mode: Adding or modifying documents is restricted to authorized administrators.",

        # RBAC & Security
        "role_student": "Student / Researcher",
        "role_admin": "Administrator",
        "admin_login_title": "Administrator Access",
        "admin_login_help": "Enter the master password to unlock administrative capabilities.",
        "admin_login_pwd": "Admin Password",
        "admin_login_btn": "Log In",
        "admin_logout_btn": "Log Out",
        "admin_auth_success": "Successfully authenticated as Administrator.",
        "admin_auth_failed": "Authentication failed: Invalid admin password.",
        "access_denied_about": "Access denied: The Project & Context view is restricted to authorized administrators.",

        # General
        "btn_analyze": "Run Analysis",
        "btn_clear": "Clear History",
    }
}

# ─────────────────────────────────────────────────────────────────────────────
# 3. KORATIERTE FORSCHUNGSFRAGEN (CLICKABLE CARDS)
# ─────────────────────────────────────────────────────────────────────────────
CURATED_QUESTIONS = {
    "de": [
        {
            "tag": "Schnittstellenprozesse",
            "title": "Kulturelle Spannungsfelder",
            "text": "Welche Spannungen entstehen an den Schnittstellen zwischen Verwaltung, Forschung und Lehre bei der Digitalisierung?"
        },
        {
            "tag": "Wirtschaftsinformatik",
            "title": "Business-IT-Alignment",
            "text": "Welche Rolle spielen Organisationskultur und das SAFe-Framework bei Russ et al. (2025) an der ZHAW?"
        },
        {
            "tag": "Organisationspädagogik",
            "title": "Lernkapazität & Barrieren",
            "text": "Welche hemmenden Barrieren des organisationalen Lernens an Hochschulen identifizieren Tintoré & Arbós (2013)?"
        },
        {
            "tag": "Empirische Befunde",
            "title": "Wissensaustausch & Leistung",
            "text": "Wie beeinflussen Information Acquisition und Knowledge Dissemination die Leistung von Universitäten laut Elbawab (2024)?"
        },
        {
            "tag": "Interdisziplinär",
            "title": "Methodischer Brückenschlag",
            "text": "Wie unterscheiden sich die Perspektiven von Wirtschaftsinformatik und Organisationspädagogik bezüglich Hochschulwandel?"
        },
        {
            "tag": "Forschungsagenda",
            "title": "Entwicklung Use Case 3",
            "text": "Welche zentralen Bausteine sollte eine Forschungsagenda zur kulturseitigen Digitalisierung von Hochschulen umfassen?"
        }
    ],
    "en": [
        {
            "tag": "Interface Processes",
            "title": "Cultural Tensions",
            "text": "What cultural tensions emerge at the interfaces between administration, research, and teaching during digitalization?"
        },
        {
            "tag": "Information Systems",
            "title": "Business-IT Alignment",
            "text": "What role do organizational culture and agile frameworks (SAFe) play in the Swiss university case study by Russ et al. (2025)?"
        },
        {
            "tag": "Organizational Pedagogy",
            "title": "Learning Barriers",
            "text": "What barriers to organizational learning capacity in higher education do Tintoré & Arbós (2013) identify?"
        },
        {
            "tag": "Empirical Findings",
            "title": "Knowledge & Performance",
            "text": "How do information acquisition and knowledge dissemination influence university performance according to Elbawab (2024)?"
        },
        {
            "tag": "Interdisciplinary",
            "title": "Bridging Perspectives",
            "text": "How do the perspectives of Business Information Systems and Organizational Pedagogy differ regarding organizational culture?"
        },
        {
            "tag": "Research Agenda",
            "title": "Use Case 3 Synthesis",
            "text": "What key pillars should a research agenda on cultural conflicts in university digitalization include?"
        }
    ]
}

# ─────────────────────────────────────────────────────────────────────────────
# 4. OPTIONEN & INITIALISIERUNG DER RAG-ENGINE
# ─────────────────────────────────────────────────────────────────────────────
MODEL_OPTIONS = {
    "DeepSeek V4.1 Flash (Empfohlen — schnell & präzise)": "deepseek-v4.1-flash-1017",
    "DeepSeek V4 Flash 0731 (Standard)": "deepseek-v4-flash-0731",
    "Mistral Large (Vertiefte Argumentation)": "mistral-large-4-1t-a52b",
}

DISCIPLINE_OPTIONS = {
    "de": {
        "Alle Disziplinen": None,
        "Wirtschaftsinformatik": "Wirtschaftsinformatik",
        "Organisationspädagogik": "Organisationspädagogik",
        "Organisationspädagogik / Hochschulforschung": "Organisationspädagogik / Hochschulforschung",
    },
    "en": {
        "All disciplines": None,
        "Business Information Systems": "Wirtschaftsinformatik",
        "Organizational Pedagogy": "Organisationspädagogik",
        "Org. Pedagogy / Higher Ed. Research": "Organisationspädagogik / Hochschulforschung",
    }
}

RESEARCH_TYPE_OPTIONS = {
    "de": {
        "Alle Orientierungen": None,
        "Deskriptiv (Status-quo & Phänomene)": "Deskriptiv",
        "Präskriptiv (Gestaltung & Methoden)": "Präskriptiv",
        "Beides (Kombinierte Beiträge)": "Beides",
    },
    "en": {
        "All orientations": None,
        "Descriptive (Empirical findings)": "Deskriptiv",
        "Prescriptive (Design & solutions)": "Präskriptiv",
        "Both (Combined contributions)": "Beides",
    }
}


@st.cache_resource(show_spinner="Initialisiere RAG-Architektur...")
def get_rag_engine() -> tuple[RAGEngine, ChromaManager, GWDGClient]:
    """Lädt die RAG-Engine, ChromaDB-Anbindung und den GWDG-Client einmalig."""
    chroma = ChromaManager()
    gwdg = GWDGClient()
    engine = RAGEngine(chroma_manager=chroma, gwdg_client=gwdg)
    return engine, chroma, gwdg


# ─────────────────────────────────────────────────────────────────────────────
# 5. PREMIUM CLEAN SAAS STYLING (CSS)
# ─────────────────────────────────────────────────────────────────────────────
def apply_saas_styling():
    """Injiziert professionelles CSS im Stil von Linear, Notion und ChatGPT."""
    st.markdown("""
    <style>
    /* Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

    :root {
        --bg-main: #F8FAFC;
        --bg-sidebar: #F1F5F9;
        --bg-card: #FFFFFF;
        --text-primary: #1E293B;
        --text-secondary: #64748B;
        --text-muted: #94A3B8;
        --border-color: #E2E8F0;
        --border-subtle: #EDF2F7;
        --primary-structural: #17365D;
        --accent-red: #B42336;
        --accent-teal: #0F766E;
        --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.05);
        --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.06), 0 2px 4px -1px rgba(0, 0, 0, 0.03);
        --shadow-lg: 0 10px 15px -3px rgba(0, 0, 0, 0.05);
    }

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
        color: var(--text-primary);
        background-color: var(--bg-main);
    }

    /* Streamlit Container Anpassung */
    .main .block-container {
        max-width: 1040px;
        padding-top: 1.8rem;
        padding-bottom: 4rem;
    }

    /* Sidebar Styling */
    [data-testid="stSidebar"] {
        background-color: var(--bg-sidebar);
        border-right: 1px solid var(--border-color);
    }

    [data-testid="stSidebar"] .block-container {
        padding-top: 1.5rem;
        padding-bottom: 2rem;
    }

    /* Brand Header in Sidebar */
    .brand-box {
        padding: 0.6rem 0.8rem 1rem 0.8rem;
        margin-bottom: 1.2rem;
        border-bottom: 1px solid var(--border-color);
    }

    .brand-tag {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: var(--primary-structural);
        background: #E2E8F0;
        padding: 3px 8px;
        border-radius: 6px;
        margin-bottom: 0.5rem;
    }

    .brand-dot {
        width: 7px;
        height: 7px;
        background-color: var(--accent-red);
        border-radius: 50%;
        display: inline-block;
    }

    .brand-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: var(--primary-structural);
        letter-spacing: -0.02em;
        margin: 0;
        line-height: 1.2;
    }

    .brand-sub {
        font-size: 0.78rem;
        color: var(--text-secondary);
        margin-top: 3px;
        line-height: 1.3;
    }

    /* Sidebar Headings */
    .sidebar-section-title {
        font-size: 0.68rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.09em;
        color: var(--text-muted);
        margin: 1.2rem 0 0.5rem 0.2rem;
    }

    /* Status Card in Sidebar */
    .status-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 0.75rem 0.85rem;
        margin-top: 1rem;
        font-size: 0.8rem;
        box-shadow: var(--shadow-sm);
    }

    .status-indicator {
        display: flex;
        align-items: center;
        gap: 7px;
        font-weight: 600;
        font-size: 0.8rem;
        margin-bottom: 0.4rem;
    }

    .status-dot-green {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #10B981;
        box-shadow: 0 0 0 2px rgba(16, 185, 129, 0.2);
    }

    .status-dot-amber {
        width: 8px;
        height: 8px;
        border-radius: 50%;
        background-color: #F59E0B;
        box-shadow: 0 0 0 2px rgba(245, 158, 11, 0.2);
    }

    .status-meta {
        color: var(--text-secondary);
        font-size: 0.76rem;
        line-height: 1.4;
    }

    /* Welcome Hero Screen */
    .welcome-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 14px;
        padding: 2rem 2.2rem;
        margin-bottom: 2rem;
        box-shadow: var(--shadow-sm);
        position: relative;
        overflow: hidden;
    }

    .welcome-card::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 4px;
        height: 100%;
        background-color: var(--accent-red);
    }

    .welcome-title {
        font-size: 1.55rem;
        font-weight: 700;
        color: var(--primary-structural);
        margin: 0 0 0.4rem 0;
        letter-spacing: -0.02em;
    }

    .welcome-context {
        font-size: 0.85rem;
        color: var(--text-secondary);
        margin-bottom: 0.9rem;
        font-weight: 500;
    }

    .welcome-text {
        font-size: 0.92rem;
        color: var(--text-primary);
        line-height: 1.6;
        margin-bottom: 0;
    }

    /* Clickable Question Cards Grid */
    .question-grid {
        display: grid;
        grid-template-columns: repeat(auto-fill, minmax(310px, 1fr));
        gap: 0.8rem;
        margin-bottom: 2rem;
    }

    .prompt-card {
        background: var(--bg-card);
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 0.9rem 1.1rem;
        transition: all 0.18s ease-in-out;
        cursor: pointer;
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        box-shadow: var(--shadow-sm);
        text-align: left;
    }

    .prompt-card:hover {
        border-color: #CBD5E1;
        box-shadow: var(--shadow-md);
        transform: translateY(-1px);
    }

    .prompt-tag {
        font-size: 0.7rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: var(--primary-structural);
        margin-bottom: 0.35rem;
    }

    .prompt-headline {
        font-weight: 600;
        font-size: 0.88rem;
        color: var(--text-primary);
        margin-bottom: 0.3rem;
    }

    .prompt-snippet {
        font-size: 0.8rem;
        color: var(--text-secondary);
        line-height: 1.4;
    }

    /* Source Citation Cards */
    .citation-container {
        background: #F8FAFC;
        border: 1px solid var(--border-color);
        border-left: 3px solid var(--primary-structural);
        border-radius: 6px;
        padding: 0.75rem 1rem;
        margin: 0.5rem 0;
        font-size: 0.86rem;
    }

    .citation-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 0.3rem;
    }

    .citation-title {
        font-weight: 600;
        color: var(--primary-structural);
        font-size: 0.88rem;
    }

    .citation-meta {
        color: var(--text-secondary);
        font-size: 0.8rem;
        display: flex;
        flex-wrap: wrap;
        gap: 0.5rem;
        align-items: center;
    }

    /* Badges */
    .badge {
        display: inline-block;
        padding: 2px 7px;
        border-radius: 4px;
        font-size: 0.72rem;
        font-weight: 600;
        letter-spacing: 0.02em;
    }

    .badge-wi {
        background-color: #E2E8F0;
        color: #334155;
    }

    .badge-op {
        background-color: #E0E7FF;
        color: #3730A3;
    }

    .badge-deskriptiv {
        background-color: #E0F2FE;
        color: #0369A1;
    }

    .badge-praeskriptiv {
        background-color: #FCE7F3;
        color: #9D174D;
    }

    .badge-beides {
        background-color: #F3E8FF;
        color: #6B21A8;
    }

    .badge-score {
        background-color: #ECFDF5;
        color: #047857;
        font-family: 'JetBrains Mono', monospace;
    }

    /* Abstention Warning Box */
    .abstention-box {
        background-color: #FFFBEB;
        border: 1px solid #FDE68A;
        border-left: 4px solid #F59E0B;
        border-radius: 8px;
        padding: 0.9rem 1.1rem;
        margin: 0.8rem 0;
        font-size: 0.88rem;
        color: #92400E;
    }

    /* Response Meta Footer */
    .response-meta-footer {
        display: flex;
        gap: 1.2rem;
        align-items: center;
        font-size: 0.76rem;
        color: var(--text-muted);
        margin-top: 0.4rem;
        padding-top: 0.3rem;
    }

    /* Workspace Guide Banner */
    .workspace-banner {
        background: #FFFFFF;
        border: 1px solid var(--border-color);
        border-radius: 10px;
        padding: 1.1rem 1.3rem;
        margin-bottom: 1.2rem;
        font-size: 0.88rem;
        box-shadow: var(--shadow-sm);
        line-height: 1.5;
    }

    /* Modern Streamlit Chat Input */
    .stChatInput > div {
        border-radius: 10px !important;
        border: 1px solid var(--border-color) !important;
        box-shadow: var(--shadow-sm) !important;
    }

    .stChatInput > div:focus-within {
        border-color: var(--primary-structural) !important;
        box-shadow: 0 0 0 2px rgba(23, 54, 93, 0.15) !important;
    }

    /* Subdued Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 500;
        font-size: 0.86rem;
        transition: all 0.15s ease;
    }

    /* Primary Button in Uni Hildesheim Red */
    .stButton > button[kind="primary"] {
        background-color: var(--accent-red) !important;
        color: #FFFFFF !important;
        border: none !important;
    }

    .stButton > button[kind="primary"]:hover {
        background-color: #8E1B2B !important;
    }

    /* Role Badges */
    .badge-role-student {
        background-color: #F1F5F9;
        color: #17365D;
        border: 1px solid #CBD5E1;
    }
    .badge-role-admin {
        background-color: #FEE2E2;
        color: #B42336;
        border: 1px solid #FCA5A5;
        font-weight: 700;
    }
    </style>
    """, unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# 6. HILFSFUNKTIONEN FÜR RENDERING & DOKUMENTENVERWALTUNG
# ─────────────────────────────────────────────────────────────────────────────
def render_citation_card(citation: SourceCitation, lang: str = "de"):
    """Rendert ein Zitat als ansprechende Karte mit verifizierten Seitenzahlen und Badges."""
    t = UI_STRINGS[lang]

    # Disziplin-Badge
    disc_class = "badge-wi" if "wirtschaft" in citation.discipline.lower() else "badge-op"

    # Forschungstyp-Badge
    rt = citation.research_type.lower() if citation.research_type else ""
    if "deskriptiv" in rt and "präskriptiv" not in rt:
        rt_badge = f'<span class="badge badge-deskriptiv">Deskriptiv</span>'
    elif "präskriptiv" in rt and "deskriptiv" not in rt:
        rt_badge = f'<span class="badge badge-praeskriptiv">Präskriptiv</span>'
    elif "beides" in rt or ("deskriptiv" in rt and "präskriptiv" in rt):
        rt_badge = f'<span class="badge badge-beides">Deskriptiv & Präskriptiv</span>'
    else:
        rt_badge = ""

    score_pct = f"{int(round(citation.relevance_score * 100))}%"

    st.markdown(f"""
    <div class="citation-container">
        <div class="citation-header">
            <div class="citation-title">{citation.short_title}</div>
            <span class="badge badge-score">{t['citation_relevance']}: {score_pct}</span>
        </div>
        <div class="citation-meta">
            <span>👤 {citation.authors} ({citation.year})</span>
            <span>📄 <strong>{citation.page_display}</strong></span>
            <span class="badge {disc_class}">{citation.discipline}</span>
            {rt_badge}
        </div>
    </div>
    """, unsafe_allow_html=True)


def handle_incremental_pdf_upload(uploaded_files, chroma: ChromaManager, lang: str, user_role: UserRole = UserRole.STUDENT):
    """Verarbeitet zusätzliche PDFs inkrementell ohne bestehende Daten zu löschen oder zu überschreiben.
    Erzwingt strikt die Administratorberechtigung im Backend (Default Deny).
    """
    # Strikter Backend-Schutz (Default Deny)
    enforce_permission(user_role, Permission.UPLOAD_DOCUMENT, "Zugriff verweigert (Default Deny): Nur Administratoren dürfen Dokumente zum Korpus hinzufügen.")

    from src.ingestion.docling_parser import DoclingParser
    from src.ingestion.chunker import AcademicChunker
    from src.ingestion.models import DocumentMetadata
    from config.settings import DATA_DIR, CATALOG_PATH
    import yaml

    t = UI_STRINGS[lang]
    parser = DoclingParser()
    chunker = AcademicChunker()
    data_dir = Path(DATA_DIR)
    data_dir.mkdir(parents=True, exist_ok=True)

    # Existierende doc_ids ermitteln
    existing_doc_ids = chroma.get_existing_doc_ids()
    processed_count = 0

    for file in uploaded_files:
        file_bytes = file.read()
        file_hash = hashlib.md5(file_bytes).hexdigest()[:8]
        file.seek(0)

        safe_stem = Path(file.name).stem[:40].replace(" ", "_")
        doc_id = f"doc_{safe_stem}_{file_hash}"

        if doc_id in existing_doc_ids:
            st.info(t["lib_upload_skip"].format(name=file.name))
            continue

        with st.spinner(f"Verarbeite '{file.name}' mit Docling & Chunker..."):
            dest_pdf = data_dir / file.name
            with open(dest_pdf, "wb") as f:
                f.write(file_bytes)

            doc_meta = DocumentMetadata(
                id=doc_id,
                filename=file.name,
                title=Path(file.name).stem.replace("_", " "),
                short_title=f"Dokument: {Path(file.name).stem[:35]}",
                authors=[],
                year=0,
                publication="",
                doi="",
                discipline="Unklassifiziert",
                research_type="Unklassifiziert",
                core_concepts=[],
                summary=""
            )

            try:
                docling_doc = parser.parse_pdf(dest_pdf, use_cache=True)
                chunks = chunker.chunk_document(docling_doc, doc_meta)

                if chunks:
                    indexed = chroma.index_chunks(chunks)
                    processed_count += 1

                    # Zu YAML hinzufügen
                    _append_doc_to_catalog(doc_meta, CATALOG_PATH)
                    st.success(f"✅ '{file.name}': {indexed} Chunks erfolgreich indexiert.")
            except Exception as e:
                st.error(f"Fehler bei '{file.name}': {str(e)}")

    if processed_count > 0:
        st.success(t["lib_upload_success"].format(count=processed_count))
        st.cache_resource.clear()
        time.sleep(1)
        st.rerun()


def _append_doc_to_catalog(doc_meta, catalog_path: Path):
    """Erweitert den Katalog atomar ohne Datenverlust."""
    import yaml
    cat_path = Path(catalog_path)
    data = {"documents": []}
    if cat_path.exists():
        with open(cat_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {"documents": []}

    existing_ids = {d.get("id") for d in data.get("documents", [])}
    if doc_meta.id not in existing_ids:
        data.setdefault("documents", []).append({
            "id": doc_meta.id,
            "filename": doc_meta.filename,
            "title": doc_meta.title,
            "short_title": doc_meta.short_title,
            "authors": doc_meta.authors,
            "year": doc_meta.year,
            "publication": doc_meta.publication,
            "doi": doc_meta.doi,
            "discipline": doc_meta.discipline,
            "research_type": doc_meta.research_type,
            "core_concepts": doc_meta.core_concepts,
            "summary": doc_meta.summary,
        })
        with open(cat_path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)


# ─────────────────────────────────────────────────────────────────────────────
# 7. HAUPTANWENDUNG (MAIN ENTRY POINT)
# ─────────────────────────────────────────────────────────────────────────────
def main():
    apply_saas_styling()

    # Engine initialisieren
    engine, chroma, gwdg = get_rag_engine()

    # Session State initialisieren
    if "messages" not in st.session_state:
        st.session_state.messages = []
    if "language" not in st.session_state:
        st.session_state.language = "de"
    if "nav_view" not in st.session_state:
        st.session_state.nav_view = "chat"
    if "pending_question" not in st.session_state:
        st.session_state.pending_question = None
    if "auth_role" not in st.session_state:
        st.session_state.auth_role = UserRole.STUDENT  # Default Deny: Jede Sitzung startet als Student/Researcher
    if "auth_token" not in st.session_state:
        st.session_state.auth_token = None

    # Administrator-Sitzungstoken validieren
    is_admin = False
    if st.session_state.auth_role == UserRole.ADMIN:
        if SecurityManager.validate_admin_token(st.session_state.auth_token):
            is_admin = True
        else:
            # Token ungültig oder abgelaufen -> Default Deny
            st.session_state.auth_role = UserRole.STUDENT
            st.session_state.auth_token = None
            if st.session_state.nav_view == "about":
                st.session_state.nav_view = "chat"

    # ─────────────────────────────────────────────────────────────────────────
    # SIDEBAR: BRANDING, NAVIGATION, EINSTELLUNGEN, SYSTEMSTATUS
    # ─────────────────────────────────────────────────────────────────────────
    with st.sidebar:
        # 1. Branding Header (rollenspezifisch)
        if not is_admin:
            st.markdown("""
            <div class="brand-box">
                <div class="brand-tag"><span class="brand-dot"></span> DigiHochX · Research Assistant</div>
                <h2 class="brand-title">Research Assistant</h2>
                <div class="brand-sub">Wissenschaftliche Literaturanalyse</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="brand-box">
                <div class="brand-tag" style="background:#FEE2E2;color:#B42336;"><span class="brand-dot" style="background:#B42336;"></span> DigiHochX · Administrator</div>
                <h2 class="brand-title">Research Assistant</h2>
                <div class="brand-sub">Uni Hildesheim · AG ISUM<br>Prof. Dr. Ralf Knackstedt · Admin</div>
            </div>
            """, unsafe_allow_html=True)

        lang = st.session_state.language
        t = UI_STRINGS[lang]

        # 2. Administrative Authentifizierung (NUR sichtbar wenn bereits Admin oder über gesicherten URL-Parameter ?admin=1)
        show_admin_param = str(st.query_params.get("admin", "")).lower() in ["1", "true", "yes"]
        if is_admin:
            st.markdown('<div class="sidebar-section-title">ADMINISTRATOR-STATUS</div>', unsafe_allow_html=True)
            st.markdown('<div style="margin-bottom:0.6rem;"><span class="badge badge-role-admin">🛡️ Administrator (Vollzugriff)</span></div>', unsafe_allow_html=True)
            if st.button(f"🚪 {t['admin_logout_btn']}", key="btn_admin_logout", use_container_width=True):
                SecurityManager.revoke_admin_token(st.session_state.auth_token)
                st.session_state.auth_role = UserRole.STUDENT
                st.session_state.auth_token = None
                if st.session_state.nav_view == "about":
                    st.session_state.nav_view = "chat"
                st.rerun()
        elif show_admin_param:
            with st.expander("🔐 Gesicherter Systemzugang", expanded=True):
                admin_pwd = st.text_input("Kennwort", type="password", key="admin_pwd_input")
                if st.button("Verifizieren", key="btn_admin_login_submit", type="primary", use_container_width=True):
                    token = SecurityManager.authenticate_admin(admin_pwd)
                    if token:
                        st.session_state.auth_token = token
                        st.session_state.auth_role = UserRole.ADMIN
                        st.success("Erfolgreich autorisiert.")
                        time.sleep(0.4)
                        st.rerun()
                    else:
                        st.error("Zugriff verweigert.")

        # 3. Primäre Aktion: Neue Unterhaltung
        if st.button(t["nav_new_chat"], use_container_width=True, type="secondary"):
            st.session_state.messages = []
            st.session_state.nav_view = "chat"
            st.rerun()

        # 4. Hauptnavigation (rollenspezifisch: "about" nur für Admins)
        st.markdown(f'<div class="sidebar-section-title">{t["sidebar_nav_title"]}</div>', unsafe_allow_html=True)

        nav_options = {
            "chat": t["nav_chat"],
            "workspace": t["nav_workspace"],
            "library": t["nav_library"]
        }
        if is_admin:
            nav_options["about"] = t["nav_about"]

        # Default Deny: Wenn ein Student versucht, auf "about" zu bleiben
        if not is_admin and st.session_state.nav_view == "about":
            st.session_state.nav_view = "chat"

        nav_keys = list(nav_options.keys())
        current_idx = nav_keys.index(st.session_state.nav_view) if st.session_state.nav_view in nav_keys else 0

        selected_nav_label = st.radio(
            "Hauptmenü",
            options=list(nav_options.values()),
            index=current_idx,
            label_visibility="collapsed"
        )

        for k, v in nav_options.items():
            if v == selected_nav_label:
                st.session_state.nav_view = k
                break

        # 5. Einstellungen (Kompakt in Expander)
        st.markdown(f'<div class="sidebar-section-title">{t["sidebar_config_title"]}</div>', unsafe_allow_html=True)

        with st.expander("⚙️ Parameter & Filter", expanded=False):
            # Sprache
            lang_choice = st.selectbox(
                t["language_label"],
                ["Deutsch", "English"],
                index=0 if st.session_state.language == "de" else 1,
                key="lang_selector"
            )
            new_lang = "de" if lang_choice == "Deutsch" else "en"
            if new_lang != st.session_state.language:
                st.session_state.language = new_lang
                st.rerun()

            # Modellwahl
            selected_model_label = st.selectbox(
                t["model_label"],
                list(MODEL_OPTIONS.keys()),
                index=0
            )
            selected_model_id = MODEL_OPTIONS[selected_model_label]

            # Disziplinfilter
            disc_options = DISCIPLINE_OPTIONS[lang]
            selected_disc_label = st.selectbox(
                t["discipline_filter_label"],
                list(disc_options.keys()),
                index=0
            )
            discipline_filter = disc_options[selected_disc_label]

            # Forschungstypfilter
            rt_options = RESEARCH_TYPE_OPTIONS[lang]
            selected_rt_label = st.selectbox(
                t["research_type_filter_label"],
                list(rt_options.keys()),
                index=0
            )
            research_type_filter = rt_options[selected_rt_label]

        # Standardwerte falls Expander nicht aufgeklappt wurde
        if "selected_model_id" not in locals():
            selected_model_id = MODEL_OPTIONS[list(MODEL_OPTIONS.keys())[0]]
            discipline_filter = None
            research_type_filter = None

        # 6. System- und Korpusstatus (rollenspezifisch)
        st.markdown(f'<div class="sidebar-section-title">{t["sidebar_system_title"]}</div>', unsafe_allow_html=True)
        corpus_stats = engine.get_corpus_stats()
        chunk_count = corpus_stats.get("total_chunks", 0)
        doc_count = len(corpus_stats.get("documents", {}))

        if gwdg.is_configured:
            status_html = f'<div class="status-indicator"><span class="status-dot-green"></span> {t["status_connected"]}</div>'
        else:
            status_html = f'<div class="status-indicator"><span class="status-dot-amber"></span> {t["status_offline"]}</div>'

        if is_admin:
            sub_status_text = t["active_collection"]
        else:
            sub_status_text = "DigiHochX Wissensbasis"

        st.markdown(f"""
        <div class="status-card">
            {status_html}
            <div class="status-meta">
                <strong>{doc_count}</strong> {t["metric_docs"]} · <strong>{chunk_count}</strong> {t["metric_chunks"]}<br>
                <span style="font-size:0.7rem;color:#94A3B8;">{sub_status_text}</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # VIEW 1: FORSCHUNGS-CHAT (MAIN CONVERSATIONAL INTERFACE)
    # ─────────────────────────────────────────────────────────────────────────
    if st.session_state.nav_view == "chat":
        # Wenn noch keine Nachrichten vorhanden sind: Klarer, kompakter Header & kuratierte Fragen
        if not st.session_state.messages:
            st.markdown("""
            <div style="margin-bottom: 1.8rem; padding-bottom: 0.8rem; border-bottom: 1px solid #E2E8F0;">
                <h1 style="font-size: 2.1rem; font-weight: 700; color: #17365D; margin: 0 0 0.25rem 0; letter-spacing: -0.02em;">DigiHochX Research Assistant</h1>
                <div style="font-size: 0.95rem; color: #64748B; font-weight: 500; letter-spacing: 0.02em;">Research Chat</div>
            </div>
            """, unsafe_allow_html=True)

            st.markdown(f"**{t['welcome_prompt_label']}**")

            # Fragenkarten in ansprechender 2-Spalten-Matrix
            col1, col2 = st.columns(2)
            curated = CURATED_QUESTIONS.get(lang, CURATED_QUESTIONS["de"])

            for i, q in enumerate(curated):
                target_col = col1 if i % 2 == 0 else col2
                with target_col:
                    card_content = f"**{q['title']}**  \n*{q['tag']}* — {q['text']}"
                    if st.button(card_content, key=f"cq_{i}", use_container_width=True):
                        st.session_state.pending_question = q["text"]
                        st.rerun()

        # Chatverlauf rendern
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

                # Quellenbelege (nur bei Assistant)
                if msg["role"] == "assistant" and msg.get("sources"):
                    with st.expander(f"📖 {t['citations_title']} ({len(msg['sources'])})", expanded=False):
                        for c in msg["sources"]:
                            render_citation_card(c, lang)

                # Abstention-Hinweis
                if msg["role"] == "assistant" and msg.get("is_abstention"):
                    st.markdown(f"""
                    <div class="abstention-box">
                        <strong>{t['abstention_title']}:</strong> {t['abstention_desc']}
                    </div>
                    """, unsafe_allow_html=True)

                # Metadaten-Leiste
                if msg["role"] == "assistant" and msg.get("model_used"):
                    st.markdown(f"""
                    <div class="response-meta-footer">
                        <span>{t['meta_model']}: <strong>{msg['model_used']}</strong></span>
                        <span>{t['meta_latency']}: <strong>{msg.get('latency', 0):.1f}s</strong></span>
                        <span>Grounding: <strong>100% Corpus-Bound</strong></span>
                    </div>
                    """, unsafe_allow_html=True)

        # Frage aus vorherigem Klick oder Chat-Input
        user_input = None
        if st.session_state.pending_question:
            user_input = st.session_state.pending_question
            st.session_state.pending_question = None
        else:
            user_input = st.chat_input(t["chat_input_placeholder"])

        if user_input:
            # 1. Nutzernachricht speichern und anzeigen
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            # 2. Assistant RAG-Generierung
            with st.chat_message("assistant"):
                with st.spinner(t["thinking_status"]):
                    start_time = time.time()
                    try:
                        resp: RAGResponse = engine.query(
                            question=user_input,
                            language=lang,
                            top_k=8,
                            discipline_filter=discipline_filter,
                            research_type_filter=research_type_filter,
                            model=selected_model_id,
                            analysis_mode="general",
                            chat_history=st.session_state.messages
                        )
                        elapsed = time.time() - start_time

                        # Falls der Nutzer einen Sprachwechsel angefordert hat, sofort anpassen
                        if resp.requested_language and resp.requested_language != st.session_state.language:
                            st.session_state.language = resp.requested_language

                        st.markdown(resp.answer)

                        if resp.sources:
                            with st.expander(f"📖 {t['citations_title']} ({len(resp.sources)})", expanded=True):
                                for c in resp.sources:
                                    render_citation_card(c, lang)

                        if resp.is_abstention:
                            st.markdown(f"""
                            <div class="abstention-box">
                                <strong>{t['abstention_title']}:</strong> {t['abstention_desc']}
                            </div>
                            """, unsafe_allow_html=True)

                        mode_label = "Conversational Dialog" if resp.is_conversational else "100% Corpus-Bound"
                        st.markdown(f"""
                        <div class="response-meta-footer">
                            <span>{t['meta_model']}: <strong>{resp.model_used}</strong></span>
                            <span>{t['meta_latency']}: <strong>{elapsed:.1f}s</strong></span>
                            <span>Status: <strong>{mode_label}</strong></span>
                        </div>
                        """, unsafe_allow_html=True)

                        # Im Verlauf speichern
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": resp.answer,
                            "sources": resp.sources,
                            "model_used": resp.model_used,
                            "latency": elapsed,
                            "is_abstention": resp.is_abstention,
                            "is_conversational": resp.is_conversational
                        })

                    except Exception as e:
                        err_str = f"Fehler bei der Forschungsanalyse: {str(e)}"
                        st.error(err_str)
                        st.session_state.messages.append({
                            "role": "assistant",
                            "content": f"⚠️ {err_str}",
                            "sources": [],
                            "model_used": "Error",
                            "latency": 0,
                            "is_abstention": False
                        })

    # ─────────────────────────────────────────────────────────────────────────
    # VIEW 2: RESEARCH WORKSPACE (METHODISCHE ANALYSEN)
    # ─────────────────────────────────────────────────────────────────────────
    elif st.session_state.nav_view == "workspace":
        st.markdown(f"## {t['nav_workspace']}")
        st.caption("Systematische methodische Werkzeuge zur Bearbeitung von Use Case 3.")

        ws_tabs = st.tabs([
            f"🔬 {t['ws_classification']}",
            f"🔗 {t['ws_interdisciplinary']}",
            f"⚡ {t['ws_tensions']}",
            f"🔍 {t['ws_gaps']}",
            f"❓ {t['ws_questions']}",
            f"📋 {t['ws_agenda']}"
        ])

        workspace_configs = [
            ("classification", t["ws_desc_classification"], "classify"),
            ("interdisciplinary", t["ws_desc_interdisciplinary"], "interdisc"),
            ("tension_analysis", t["ws_desc_tensions"], "tensions"),
            ("research_gaps", t["ws_desc_gaps"], "gaps"),
            ("research_questions", t["ws_desc_questions"], "questions"),
            ("research_agenda", t["ws_desc_agenda"], "agenda"),
        ]

        for idx, (mode, desc, prefix) in enumerate(workspace_configs):
            with ws_tabs[idx]:
                st.markdown(f'<div class="workspace-banner">{desc}</div>', unsafe_allow_html=True)

                col_input, col_action = st.columns([4, 1])
                with col_input:
                    ws_query = st.text_area(
                        "Spezifische Forschungsfrage für diese methodische Analyse:",
                        height=90,
                        key=f"ws_input_{prefix}",
                        placeholder="Geben Sie hier Ihre spezifische Analysefrage ein..."
                    )
                with col_action:
                    st.write("")
                    st.write("")
                    run_btn = st.button(t["btn_analyze"], key=f"btn_{prefix}", type="primary", use_container_width=True)

                if run_btn and ws_query.strip():
                    with st.spinner(t["thinking_status"]):
                        start_t = time.time()
                        try:
                            res = engine.query(
                                question=ws_query,
                                language=lang,
                                top_k=8,
                                discipline_filter=discipline_filter,
                                research_type_filter=research_type_filter,
                                model=selected_model_id,
                                analysis_mode=mode,
                                chat_history=st.session_state.messages
                            )
                            el = time.time() - start_t

                            st.markdown("### Analyseergebnis")
                            st.markdown(res.answer)

                            if res.sources:
                                with st.expander(f"📖 {t['citations_title']} ({len(res.sources)})", expanded=True):
                                    for c in res.sources:
                                        render_citation_card(c, lang)

                            if res.is_abstention:
                                st.markdown(f"""
                                <div class="abstention-box">
                                    <strong>{t['abstention_title']}:</strong> {t['abstention_desc']}
                                </div>
                                """, unsafe_allow_html=True)

                            st.caption(f"{t['meta_model']}: {res.model_used} · {t['meta_latency']}: {el:.1f}s")
                        except Exception as e:
                            st.error(f"Fehler: {str(e)}")

    # ─────────────────────────────────────────────────────────────────────────
    # VIEW 3: DOKUMENTENBIBLIOTHEK (SAAS DOCUMENT INVENTORY & UPLOAD)
    # ─────────────────────────────────────────────────────────────────────────
    elif st.session_state.nav_view == "library":
        st.markdown(f"## {t['lib_title']}")
        st.markdown(f"<p style='color:#64748B;font-size:0.9rem;'>{t['lib_desc']}</p>", unsafe_allow_html=True)

        corpus_stats = engine.get_corpus_stats()
        docs = corpus_stats.get("documents", {})

        # Metriken-Übersicht
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Dokumente", len(docs))
        m2.metric("Indexierte Chunks", corpus_stats.get("total_chunks", 0))
        m3.metric("Disziplinen", len(corpus_stats.get("by_discipline", {})))
        m4.metric("Forschungstypen", len(corpus_stats.get("by_research_type", {})))

        st.markdown("---")

        # Upload-Bereich (Ausschließlich für autorisierte Administratoren)
        if is_admin:
            with st.expander(f"📤 {t['lib_upload_header']}", expanded=False):
                uploaded = st.file_uploader(
                    t["lib_upload_help"],
                    type=["pdf"],
                    accept_multiple_files=True,
                    key="lib_file_uploader"
                )
                if uploaded:
                    if st.button(t["lib_upload_btn"], type="primary"):
                        handle_incremental_pdf_upload(uploaded, chroma, lang, user_role=st.session_state.auth_role)

        # Dokumentkarten
        if not docs:
            st.info(t["lib_empty"])
        else:
            for doc_id, info in docs.items():
                disc = info.get("discipline", "Wissenschaft")
                disc_class = "badge-wi" if "wirtschaft" in disc.lower() else "badge-op"
                rt = info.get("research_type", "")
                
                rt_badge_html = ""
                if "deskriptiv" in rt.lower() and "präskriptiv" not in rt.lower():
                    rt_badge_html = '<span class="badge badge-deskriptiv">Deskriptiv</span>'
                elif "präskriptiv" in rt.lower() and "deskriptiv" not in rt.lower():
                    rt_badge_html = '<span class="badge badge-praeskriptiv">Präskriptiv</span>'
                elif "beides" in rt.lower() or ("deskriptiv" in rt.lower() and "präskriptiv" in rt.lower()):
                    rt_badge_html = '<span class="badge badge-beides">Deskriptiv & Präskriptiv</span>'

                st.markdown(f"""
                <div style="background:#FFFFFF;border:1px solid #E2E8F0;border-radius:10px;padding:1.2rem;margin-bottom:1rem;box-shadow:0 1px 3px rgba(0,0,0,0.04);">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;">
                        <div>
                            <div style="font-size:1.05rem;font-weight:700;color:#17365D;margin-bottom:0.25rem;">{info.get('short_title', doc_id)}</div>
                            <div style="font-size:0.82rem;color:#64748B;margin-bottom:0.5rem;">👤 {info.get('authors', 'N/A')} ({info.get('year', 'N/A')})</div>
                        </div>
                        <div style="text-align:right;">
                            <span class="badge {disc_class}">{disc}</span>
                            {rt_badge_html}
                            <div style="font-size:0.78rem;color:#0F766E;font-weight:600;margin-top:0.35rem;">● {info.get('chunk_count', 0)} Chunks im Vektorindex</div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

    # ─────────────────────────────────────────────────────────────────────────
    # VIEW 4: PROJEKT & KONTEXT (DIGIHOCHX FACHLICHE GRUNDLAGE - NUR ADMIN)
    # ─────────────────────────────────────────────────────────────────────────
    elif st.session_state.nav_view == "about":
        # Strikte Backend- und UI-Zugriffskontrolle (Default Deny)
        if not is_admin:
            st.error(t["access_denied_about"])
            st.session_state.nav_view = "chat"
            st.rerun()

        st.markdown(f"## {t['nav_about']}")
        st.markdown("""
        ### Wissenschaftlicher Rahmen: DigiHochX

        **Offizieller Projekttitel:**  
        *Kulturelle Konflikte der digitalen Transformation in Schnittstellenprozessen an Hochschulen (DigiHochX)*

        #### 1. Projektbeschreibung
        DigiHochX befasst sich mit der grundlagentheoretischen Erforschung von organisationskulturellen Konflikten
        in digitalisierten Prozessen zwischen **Verwaltung**, **Forschung** und **Lehre** an Hochschulen.
        Mittels einer organisationstechnografischen Analyse werden Typiken organisationskultureller Konflikte
        an digitalisierten Schnittstellenprozessen analysiert und aus Sicht der kulturellen Prozessmodellierung theoretisiert.
        
        Darauf aufbauend werden Lösungsansätze eines integrativen Prozessmanagements zur Bearbeitung konflikthafter
        digitalisierter Schnittstellenprozesse entwickelt und in eine allgemeine Forschungsagenda übersetzt.

        #### 2. Unser Anwendungsfall: Use Case 3
        **Ziel:** Unterstützung von Forschenden (inklusive Studierenden) bei der systematischen Entwicklung von
        Forschungsagenden zur wissenschaftlichen Kommunikation der Projektergebnisse.
        
        Dabei werden zwei zentrale wissenschaftliche Perspektiven integriert:
        - **Organisationspädagogik:** Organisationskultur, organisationale Lernprozesse, Lernkultur, organisationale Veränderung.
        - **Wirtschaftsinformatik:** Digitalisierung von Hochschulen, Informationssysteme, Schnittstellenprozesse, Prozessmodellierung, integratives Prozessmanagement.

        #### 3. Zentrale methodische Unterscheidung
        - **Deskriptive Forschung:** Beschreibt und analysiert bestehende Zustände, Phänomene, empirische Beobachtungen und reale Barrieren.
        - **Präskriptive Forschung:** Entwickelt und begründet Gestaltungsansätze, Lösungsansätze, Handlungsempfehlungen, Methoden oder Artefakte.
        - **Integrierte Sicht:** Deskriptive empirische Befunde dienen als fundierte Grundlage für präskriptive Gestaltungsvorschläge.

        #### 4. Akademisches Umfeld
        - **Arbeitsgruppe:** Informationssysteme und Unternehmensmodellierung (ISUM)
        - **Leitung:** Prof. Dr. Ralf Knackstedt
        - **Universität:** Universität Hildesheim
        - **Projektform:** IT-Studienprojekt Master – Chatbot-Werkstatt
        """)


if __name__ == "__main__":
    main()

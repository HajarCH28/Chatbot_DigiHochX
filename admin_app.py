"""
DigiHochX Research Assistant - Dediziertes Administrations-Dashboard
=====================================================================
Eigenständige Anwendung für autorisierte Administratoren des Projekts DigiHochX.
Bietet Korpusverwaltung, inkrementelles Indexieren, Vektor-Statistiken und Audit-Logs.

Start:
    streamlit run admin_app.py --server.port 8502
"""

import sys
import time
from pathlib import Path

# Sicherstellen, dass das Projektverzeichnis im Modulpfad liegt
ROOT_DIR = Path(__file__).resolve().parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

import streamlit as st
import yaml

from src.core.rag_engine import RAGEngine
from src.vectorstore.chroma_manager import ChromaManager
from src.security.rbac import SecurityManager, UserRole, Permission, require_permission
from app import handle_incremental_pdf_upload

# ─────────────────────────────────────────────────────────────────────────────
# SEITENKONFIGURATION
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DigiHochX - Admin Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ─────────────────────────────────────────────────────────────────────────────
# CUSTOM CSS (ADMIN THEME)
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    :root {
        --primary-admin: #1E293B;
        --accent-admin: #B42336;
        --border-color: #E2E8F0;
    }
    .admin-header {
        padding: 1.2rem 1.5rem;
        background: #FFFFFF;
        border-bottom: 2px solid #B42336;
        border-radius: 8px;
        margin-bottom: 1.5rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .admin-title {
        font-size: 1.6rem;
        font-weight: 700;
        color: #1E293B;
        margin: 0;
    }
    .admin-subtitle {
        font-size: 0.9rem;
        color: #64748B;
        margin-top: 0.2rem;
    }
    .card {
        background: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 1.2rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 2px rgba(0,0,0,0.03);
    }
    .badge-admin {
        background-color: #FEE2E2;
        color: #B42336;
        padding: 0.2rem 0.6rem;
        border-radius: 6px;
        font-weight: 600;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE INITIALISIERUNG
# ─────────────────────────────────────────────────────────────────────────────
if "admin_token" not in st.session_state:
    st.session_state.admin_token = None
if "admin_role" not in st.session_state:
    st.session_state.admin_role = UserRole.STUDENT

is_authenticated = False
if st.session_state.admin_token:
    if SecurityManager.validate_admin_token(st.session_state.admin_token):
        is_authenticated = True
        st.session_state.admin_role = UserRole.ADMIN
    else:
        st.session_state.admin_token = None
        st.session_state.admin_role = UserRole.STUDENT

# ─────────────────────────────────────────────────────────────────────────────
# LOGIN-BILDSCHIRM (WENN NICHT AUTHENTIFIZIERT)
# ─────────────────────────────────────────────────────────────────────────────
if not is_authenticated:
    st.markdown("""
    <div style="max-width: 480px; margin: 4rem auto; padding: 2rem; background: #FFFFFF; border: 1px solid #CBD5E1; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.06);">
        <div style="text-align: center; margin-bottom: 1.5rem;">
            <div style="font-size: 2.2rem; margin-bottom: 0.5rem;">🛡️</div>
            <h2 style="color: #1E293B; margin: 0; font-size: 1.4rem;">DigiHochX Administration</h2>
            <p style="color: #64748B; font-size: 0.85rem; margin-top: 0.4rem;">Nur für autorisierte Systemverwalter</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("admin_login_form"):
            pwd = st.text_input("Master-Passwort", type="password", placeholder="Admin-Kennwort eingeben")
            submitted = st.form_submit_button("Authentifizieren", use_container_width=True, type="primary")

            if submitted:
                token = SecurityManager.authenticate_admin(pwd)
                if token:
                    st.session_state.admin_token = token
                    st.session_state.admin_role = UserRole.ADMIN
                    st.success("Erfolgreich angemeldet. Weiterleitung...")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Authentifizierung fehlgeschlagen: Ungültiges Passwort.")
                    time.sleep(0.5)

    st.stop()

# ─────────────────────────────────────────────────────────────────────────────
# AUTHENTIFIZIERTE ADMINISTRATIONS-OBERFLÄCHE
# ─────────────────────────────────────────────────────────────────────────────
@st.cache_resource
def get_engine():
    return RAGEngine()

@st.cache_resource
def get_chroma():
    return ChromaManager()

engine = get_engine()
chroma = get_chroma()

# Sidebar
with st.sidebar:
    st.markdown("""
    <div style="padding: 0.5rem 0 1rem 0;">
        <span class="badge-admin">🛡️ Administrator-Modus</span>
        <h3 style="margin: 0.5rem 0 0.1rem 0; color: #1E293B;">DigiHochX Admin</h3>
        <p style="font-size: 0.8rem; color: #64748B; margin: 0;">Systemverwaltung & Vektorindex</p>
    </div>
    """, unsafe_allow_html=True)

    menu = st.radio(
        "Verwaltungsbereich",
        [
            "📊 Systemstatus & Übersicht",
            "📤 Dokumenten-Upload & Inkrementelle Indexierung",
            "📚 Dokumentenkatalog (YAML)",
            "⚙️ Vektordatenbank & Wartung",
            "🔒 Sicherheitsstatus & Audit-Logs"
        ],
        index=0
    )

    st.markdown("---")
    if st.button("🚪 Abmelden", use_container_width=True):
        SecurityManager.revoke_admin_token(st.session_state.admin_token)
        st.session_state.admin_token = None
        st.session_state.admin_role = UserRole.STUDENT
        st.rerun()

# Hauptbereich Header
st.markdown("""
<div class="admin-header">
    <div class="admin-title">DigiHochX System- & Datenverwaltung</div>
    <div class="admin-subtitle">Universität Hildesheim · Arbeitsbereich Informationssysteme und Unternehmensmodellierung (ISUM)</div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1: SYSTEMSTATUS & ÜBERSICHT
# ─────────────────────────────────────────────────────────────────────────────
if menu == "📊 Systemstatus & Übersicht":
    st.subheader("Systemstatus & Index-Kennzahlen")

    stats = engine.get_corpus_stats()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Indexierte Dokumente", len(stats.get("documents", {})))
    c2.metric("Gesamte Vektor-Chunks", stats.get("total_chunks", 0))
    c3.metric("Wirtschaftsinformatik Chunks", stats.get("by_discipline", {}).get("Wirtschaftsinformatik", 0))
    c4.metric("Organisationspädagogik Chunks", stats.get("by_discipline", {}).get("Organisationspädagogik", 0))

    st.markdown("---")
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("### GWDG Academic Cloud Verbindung")
        llm_status = engine.gwdg.test_connection()
        if llm_status.get("authenticated"):
            st.success(f"✅ GWDG API verbunden: {llm_status.get('model')} ({llm_status.get('latency_ms', 0):.0f} ms)")
        else:
            st.warning(f"⚠️ GWDG Status: {llm_status.get('error', 'Nicht konfiguriert')}")

    with col_b:
        st.markdown("### ChromaDB Vector Store")
        st.info(f"Vektor-Dimension: 384 (sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)\n\nPersistiert in: `chroma_db/`")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2: DOKUMENTEN-UPLOAD & INKREMENTELLE INDEXIERUNG
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "📤 Dokumenten-Upload & Inkrementelle Indexierung":
    st.subheader("Neues wissenschaftliches Dokument hochladen")
    st.markdown("""
    Laden Sie ein oder mehrere PDF-Dokumente hoch. Jedes Dokument wird mit **Docling** geparst, 
    semantisch segmentiert und **inkrementell** zu ChromaDB hinzugefügt, ohne bestehende Chunks zu löschen.
    """)

    uploaded_files = st.file_uploader(
        "PDF-Dateien auswählen",
        type=["pdf"],
        accept_multiple_files=True,
        help="Dateien werden im Verzeichnis Data/ abgelegt und im Vektorindex erfasst."
    )

    if uploaded_files:
        st.info(f"{len(uploaded_files)} Datei(en) bereitgestellt.")
        if st.button("Dokument(e) inkrementell verarbeiten & indexieren", type="primary"):
            handle_incremental_pdf_upload(uploaded_files, chroma, language="de", user_role=st.session_state.admin_role)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3: DOKUMENTENKATALOG (YAML)
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "📚 Dokumentenkatalog (YAML)":
    st.subheader("Dokumentenkatalog: `config/documents_catalog.yaml`")

    catalog_path = ROOT_DIR / "config" / "documents_catalog.yaml"
    if catalog_path.exists():
        with open(catalog_path, "r", encoding="utf-8") as f:
            catalog_content = f.read()

        st.text_area("YAML-Konfiguration (Schreibschutz)", catalog_content, height=450)
    else:
        st.warning("Katalogdatei nicht gefunden.")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 4: VEKTORDATENBANK & WARTUNG
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "⚙️ Vektordatenbank & Wartung":
    st.subheader("ChromaDB Wartung & Re-Indexierung")

    stats = engine.get_corpus_stats()
    st.write(f"Aktuelle Collection: **`digihochx_research_agenda`** ({stats.get('total_chunks', 0)} Chunks)")

    st.warning("Achtung: Die vollständige Re-Indexierung löscht die bestehenden Vektoren und baut den Index aus den Rohdateien in `Data/` neu auf.")

    confirm = st.checkbox("Ich bestätige, dass ich den Vektorindex neu aufbauen möchte.")
    if st.button("Vollständige Re-Indexierung starten", type="secondary", disabled=not confirm):
        if not SecurityManager.check_permission(st.session_state.admin_role, Permission.REINDEX_DATABASE):
            st.error("Berechtigung verweigert.")
        else:
            with st.spinner("Re-Indexierung läuft..."):
                try:
                    from scripts.build_vectorstore import main as run_indexing
                    run_indexing()
                    st.success("Re-Indexierung erfolgreich abgeschlossen!")
                    time.sleep(1)
                    st.rerun()
                except Exception as e:
                    st.error(f"Fehler bei der Re-Indexierung: {e}")

# ─────────────────────────────────────────────────────────────────────────────
# TAB 5: SICHERHEITSSTATUS & AUDIT-LOGS
# ─────────────────────────────────────────────────────────────────────────────
elif menu == "🔒 Sicherheitsstatus & Audit-Logs":
    st.subheader("Rollenbasierte Zugriffskontrolle (RBAC) & Sicherheitsaudits")

    st.markdown("""
    - **Aktuelle Sitzung:** Rolle `UserRole.ADMIN`
    - **Authentifizierung:** PBKDF2-HMAC-SHA256 (100.000 Iterationen)
    - **Session Token:** Gesichert mit time-constant comparison (`hmac.compare_digest`)
    - **Berechtigungsmatrix:**
        - Student/Researcher: Lesemodus (Chat, Workspace, Dokumentkatalog)
        - Administrator: Vollzugriff (Upload, Löschen, Re-Indexierung, Metadaten)
    """)

    st.markdown("### Sicherheitsüberprüfungen im Code")
    st.code("""
    # Absicherung von Schreiboperationen:
    @require_permission(Permission.UPLOAD_DOCUMENT)
    def handle_incremental_pdf_upload(files, chroma, language, user_role):
        ...
    """, language="python")


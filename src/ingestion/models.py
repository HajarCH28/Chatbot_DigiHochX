from typing import List, Optional
from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):
    """Vollständige wissenschaftliche Metadaten eines akademischen Dokuments."""
    id: str = Field(description="Eindeutige Kennung des Dokuments")
    filename: str = Field(description="Name der PDF-Datei auf der Festplatte")
    title: str = Field(description="Vollständiger Titel der Publikation")
    short_title: str = Field(description="Kurztitel / Akademische Standardreferenz")
    authors: List[str] = Field(default_factory=list, description="Liste der Autoren")
    year: int = Field(description="Erscheinungsjahr")
    publication: str = Field(description="Zeitschrift, Konferenz oder Verlag")
    doi: Optional[str] = Field(default="", description="DOI-Identifikator oder URL")
    discipline: str = Field(description="Wirtschaftsinformatik, Organisationspädagogik o.ä.")
    research_type: str = Field(description="Deskriptiv, Präskriptiv oder Beides")
    core_concepts: List[str] = Field(default_factory=list, description="Zentrale theoretische Konzepte")
    summary: str = Field(default="", description="Akademische Zusammenfassung des Dokuments")

class ChunkMetadata(BaseModel):
    """Angereicherte Metadaten pro Chunk für RAG und Zitation."""
    doc_id: str
    doc_title: str
    short_title: str
    authors_str: str
    year: int
    discipline: str
    research_type: str
    page_numbers: List[int]
    page_display: str  # z. B. 'S. 331' oder 'pp. 331-332'
    headings: List[str] = Field(default_factory=list)

class TextChunk(BaseModel):
    """Strukturiertes Textsegment, bereit für Vektorindexierung und RAG."""
    chunk_id: str
    text: str
    metadata: ChunkMetadata

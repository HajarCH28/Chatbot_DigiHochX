import logging
from pathlib import Path
from typing import Dict, List, Optional

from config.settings import DATA_DIR
from src.ingestion.chunker import AcademicChunker
from src.ingestion.docling_parser import DoclingParser
from src.ingestion.models import TextChunk
from src.metadata.catalog_manager import CatalogManager

logger = logging.getLogger(__name__)

class IngestionPipeline:
    """Orchestriert Docling-Konvertierung, akademisches Chunking und Metadaten-Anreicherung."""

    def __init__(
        self,
        catalog_manager: Optional[CatalogManager] = None,
        parser: Optional[DoclingParser] = None,
        chunker: Optional[AcademicChunker] = None,
        data_dir: Path = DATA_DIR
    ):
        self.catalog_manager = catalog_manager or CatalogManager()
        self.parser = parser or DoclingParser()
        self.chunker = chunker or AcademicChunker()
        self.data_dir = data_dir

    def _find_pdf_path(self, filename: str) -> Path:
        """Findet die PDF-Datei im Data-Ordner, auch bei Encoding-Variationen."""
        exact_path = self.data_dir / filename
        if exact_path.exists():
            return exact_path

        # Groß-/Kleinschreibung- und Akzent-unabhängige Suche
        norm_name = filename.lower()
        for p in self.data_dir.glob("*.pdf"):
            if p.name.lower() == norm_name or p.stem.lower()[:30] in norm_name:
                return p
                
        raise FileNotFoundError(f"PDF nicht gefunden: {filename} in {self.data_dir}")

    def run(self, use_cache: bool = True) -> List[TextChunk]:
        """Führt die vollständige Pipeline für alle Dokumente im Katalog aus."""
        all_documents = self.catalog_manager.list_all()
        logger.info("Starte Ingestion für %d Dokument(e)...", len(all_documents))

        all_chunks: List[TextChunk] = []

        for meta in all_documents:
            pdf_path = self._find_pdf_path(meta.filename)
            logger.info("Verarbeite: %s (%s)", meta.short_title, pdf_path.name)
            
            # 1. Docling-Konvertierung
            doc = self.parser.parse_pdf(pdf_path, use_cache=use_cache)
            
            # 2. Chunking und Anreicherung
            doc_chunks = self.chunker.chunk_document(doc, meta)
            logger.info("  -> %d Segmente erfolgreich generiert", len(doc_chunks))
            
            all_chunks.extend(doc_chunks)

        logger.info("Ingestion abgeschlossen: %d Segmente insgesamt.", len(all_chunks))
        return all_chunks

    def get_stats(self, chunks: List[TextChunk]) -> Dict:
        """Berechnet deskriptive Statistiken des segmentierten Korpus."""
        by_doc: Dict[str, int] = {}
        by_discipline: Dict[str, int] = {}
        by_research_type: Dict[str, int] = {}
        page_counts: Dict[str, set] = {}

        for c in chunks:
            m = c.metadata
            by_doc[m.short_title] = by_doc.get(m.short_title, 0) + 1
            by_discipline[m.discipline] = by_discipline.get(m.discipline, 0) + 1
            by_research_type[m.research_type] = by_research_type.get(m.research_type, 0) + 1
            if m.doc_id not in page_counts:
                page_counts[m.doc_id] = set()
            page_counts[m.doc_id].update(m.page_numbers)

        return {
            "total_chunks": len(chunks),
            "by_document": by_doc,
            "by_discipline": by_discipline,
            "by_research_type": by_research_type,
            "pages_per_doc": {k: len(v) for k, v in page_counts.items()}
        }

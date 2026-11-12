from pathlib import Path
from typing import Dict, List, Optional
import yaml

from config.settings import CATALOG_PATH, DATA_DIR
from src.ingestion.models import DocumentMetadata

class CatalogManager:
    """Lädt und verwaltet den Katalog der wissenschaftlichen Dokumentmetadaten."""

    def __init__(self, catalog_path: Path = CATALOG_PATH):
        self.catalog_path = catalog_path
        self._documents: Dict[str, DocumentMetadata] = {}
        self._filename_to_id: Dict[str, str] = {}
        self.load()

    def load(self) -> None:
        """Lädt den YAML-Katalog und validiert die Pydantic-Modelle."""
        if not self.catalog_path.exists():
            raise FileNotFoundError(f"Katalog nicht gefunden: {self.catalog_path}")

        with open(self.catalog_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        raw_docs = data.get("documents", [])
        for doc_data in raw_docs:
            doc_meta = DocumentMetadata(**doc_data)
            self._documents[doc_meta.id] = doc_meta
            self._filename_to_id[doc_meta.filename] = doc_meta.id

    def get_document(self, doc_id: str) -> Optional[DocumentMetadata]:
        return self._documents.get(doc_id)

    def get_by_filename(self, filename: str) -> Optional[DocumentMetadata]:
        doc_id = self._filename_to_id.get(filename)
        if doc_id:
            return self._documents.get(doc_id)
        # Annähernde Suche (Encoding-unabhängig)
        for fname, d_id in self._filename_to_id.items():
            if fname.lower() in filename.lower() or filename.lower() in fname.lower():
                return self._documents.get(d_id)
        return None

    def list_all(self) -> List[DocumentMetadata]:
        return list(self._documents.values())

    def get_by_discipline(self, discipline: str) -> List[DocumentMetadata]:
        return [doc for doc in self._documents.values() if doc.discipline.lower() == discipline.lower()]

    def get_by_research_type(self, research_type: str) -> List[DocumentMetadata]:
        """Gibt Dokumente eines bestimmten Forschungstyps zurück."""
        return [doc for doc in self._documents.values() if doc.research_type.lower() == research_type.lower()]

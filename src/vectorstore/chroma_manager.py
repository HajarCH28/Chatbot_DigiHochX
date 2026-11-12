import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import chromadb
from chromadb.config import Settings
from pydantic import BaseModel, Field

from config.settings import CHROMA_COLLECTION_NAME, CHROMA_DB_DIR
from src.ingestion.models import TextChunk
from src.vectorstore.embeddings import MultilingualEmbedder

logger = logging.getLogger(__name__)

class SearchResult(BaseModel):
    """Angereichertes Ergebnis einer semantischen Suche mit vollständiger Quellennachvollziehbarkeit."""
    chunk_id: str
    text: str
    doc_id: str
    doc_title: str
    short_title: str
    authors: str
    year: int
    discipline: str
    research_type: str
    page_display: str
    page_numbers: List[int] = Field(default_factory=list)
    headings: List[str] = Field(default_factory=list)
    score: float = Field(description="Kosinus-Ähnlichkeitswert (zwischen 0 und 1)")

class ChromaManager:
    """Manager für lokale Persistenz und semantische Suche mit ChromaDB."""

    def __init__(
        self,
        db_path: Path = CHROMA_DB_DIR,
        collection_name: str = CHROMA_COLLECTION_NAME,
        embedder: Optional[MultilingualEmbedder] = None
    ):
        self.db_path = db_path
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.embedder = embedder or MultilingualEmbedder()

        # Lokaler persistenter ChromaDB-Client
        self.client = chromadb.PersistentClient(
            path=str(self.db_path),
            settings=Settings(anonymized_telemetry=False)
        )
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("ChromaDB initialisiert unter: %s (Collection: %s)", self.db_path, self.collection_name)

    def count(self) -> int:
        """Gibt die Gesamtzahl der indexierten Segmente zurück."""
        return self.collection.count()

    def reset_collection(self) -> None:
        """Löscht und erstellt die Collection für eine saubere Neuindexierung neu."""
        try:
            self.client.delete_collection(self.collection_name)
        except Exception:
            pass
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        logger.info("Collection %s zurückgesetzt.", self.collection_name)

    def get_existing_doc_ids(self) -> set:
        """Gibt die Menge aller bereits indexierten doc_ids zurück."""
        try:
            data = self.collection.get(include=["metadatas"])
            return {m.get("doc_id", "") for m in data.get("metadatas", [])}
        except Exception:
            return set()

    def index_chunks(self, chunks: List[TextChunk], batch_size: int = 64) -> int:
        """Indexiert Segmente mit Embeddings und flachen Metadaten für ChromaDB."""
        if not chunks:
            logger.warning("Keine Segmente zum Indexieren.")
            return 0

        logger.info("Berechne Embeddings für %d Segmente...", len(chunks))
        texts = [c.text for c in chunks]
        embeddings = self.embedder.embed_documents(texts, batch_size=batch_size)

        total_indexed = 0
        for i in range(0, len(chunks), batch_size):
            batch_chunks = chunks[i:i + batch_size]
            batch_embeddings = embeddings[i:i + batch_size]

            ids = [c.chunk_id for c in batch_chunks]
            documents = [c.text for c in batch_chunks]

            # ChromaDB erfordert Metadaten als primitive Typen (str, int, float, bool)
            metadatas = []
            for c in batch_chunks:
                m = c.metadata
                flat_meta: Dict[str, Any] = {
                    "doc_id": m.doc_id,
                    "doc_title": m.doc_title,
                    "short_title": m.short_title,
                    "authors": m.authors_str,
                    "year": m.year,
                    "discipline": m.discipline,
                    "research_type": m.research_type,
                    "page_display": m.page_display,
                    "first_page": m.page_numbers[0] if m.page_numbers else 1,
                    "page_numbers_csv": ",".join(map(str, m.page_numbers)),
                    "headings_str": " > ".join(m.headings) if m.headings else ""
                }
                metadatas.append(flat_meta)

            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=batch_embeddings,
                metadatas=metadatas
            )
            total_indexed += len(batch_chunks)

        logger.info("Indexierung abgeschlossen: %d Segmente in ChromaDB gespeichert.", total_indexed)
        return total_indexed

    def search(
        self,
        query: str,
        top_k: int = 5,
        where: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """Führt eine mehrsprachige semantische Vektorsuche mit optionalen Metadatenfiltern aus."""
        if not query.strip():
            return []

        query_vector = self.embedder.embed_query(query)
        kwargs: Dict[str, Any] = {
            "query_embeddings": [query_vector],
            "n_results": top_k
        }
        if where:
            kwargs["where"] = where

        results = self.collection.query(**kwargs)

        search_results: List[SearchResult] = []
        if not results or not results.get("ids") or not results["ids"][0]:
            return []

        ids = results["ids"][0]
        docs = results["documents"][0] if results.get("documents") else []
        metas = results["metadatas"][0] if results.get("metadatas") else []
        distances = results["distances"][0] if results.get("distances") else []

        for idx, chunk_id in enumerate(ids):
            text = docs[idx] if idx < len(docs) else ""
            meta = metas[idx] if idx < len(metas) else {}
            dist = distances[idx] if idx < len(distances) else 0.0
            # Bei ChromaDB Kosinus-Distanz: Ähnlichkeit ≈ 1 - Distanz
            score = max(0.0, min(1.0, 1.0 - dist))

            # Flache Listen rekonstruieren
            page_numbers_csv = meta.get("page_numbers_csv", "")
            page_numbers = [int(p) for p in page_numbers_csv.split(",") if p.strip().isdigit()]
            headings_str = meta.get("headings_str", "")
            headings = [h.strip() for h in headings_str.split(" > ") if h.strip()]

            search_results.append(SearchResult(
                chunk_id=chunk_id,
                text=text,
                doc_id=meta.get("doc_id", ""),
                doc_title=meta.get("doc_title", ""),
                short_title=meta.get("short_title", ""),
                authors=meta.get("authors", ""),
                year=int(meta.get("year", 0)),
                discipline=meta.get("discipline", ""),
                research_type=meta.get("research_type", ""),
                page_display=meta.get("page_display", "p. N/A"),
                page_numbers=page_numbers,
                headings=headings,
                score=round(score, 4)
            ))

        return search_results

    def get_chunks_by_ids(self, ids: List[str]) -> List[SearchResult]:
        """Ruft Chunks anhand ihrer eindeutigen IDs direkt aus ChromaDB ab."""
        if not ids:
            return []
        try:
            results = self.collection.get(ids=ids, include=["documents", "metadatas"])
            if not results or not results.get("ids"):
                return []

            retrieved: List[SearchResult] = []
            for idx, chunk_id in enumerate(results["ids"]):
                text = results["documents"][idx] if idx < len(results["documents"]) else ""
                meta = results["metadatas"][idx] if idx < len(results["metadatas"]) else {}
                page_numbers_csv = meta.get("page_numbers_csv", "")
                page_numbers = [int(p) for p in page_numbers_csv.split(",") if p.strip().isdigit()]
                headings_str = meta.get("headings_str", "")
                headings = [h.strip() for h in headings_str.split(" > ") if h.strip()]

                retrieved.append(SearchResult(
                    chunk_id=chunk_id,
                    text=text,
                    doc_id=meta.get("doc_id", ""),
                    doc_title=meta.get("doc_title", ""),
                    short_title=meta.get("short_title", ""),
                    authors=meta.get("authors", ""),
                    year=int(meta.get("year", 0)),
                    discipline=meta.get("discipline", ""),
                    research_type=meta.get("research_type", ""),
                    page_display=meta.get("page_display", "p. N/A"),
                    page_numbers=page_numbers,
                    headings=headings,
                    score=0.55
                ))
            return retrieved
        except Exception as e:
            logger.warning("Fehler beim Abruf von Chunks nach IDs: %s", e)
            return []


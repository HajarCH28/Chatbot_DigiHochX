import logging
from typing import List
from sentence_transformers import SentenceTransformer

from config.settings import DEFAULT_EMBEDDING_MODEL

logger = logging.getLogger(__name__)

class MultilingualEmbedder:
    """Manager für mehrsprachige Embeddings (Deutsch, Englisch)."""

    def __init__(self, model_name: str = DEFAULT_EMBEDDING_MODEL):
        self.model_name = model_name
        logger.info("Lade mehrsprachiges Embedding-Modell: %s", model_name)
        # Modell ist bereits lokal im Cache, Laden erfolgt 100% offline
        self.model = SentenceTransformer(model_name)
        # Dimension sauber ermitteln je nach sentence-transformers-Version
        if hasattr(self.model, "get_embedding_dimension"):
            self.dimension = self.model.get_embedding_dimension()
        else:
            self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info("Modell erfolgreich geladen (Vektordimension: %d)", self.dimension)

    def embed_query(self, query: str) -> List[float]:
        """Vektorisiert eine Nutzeranfrage (Deutsch oder Englisch)."""
        vector = self.model.encode(query, normalize_embeddings=True)
        return vector.tolist()

    def embed_documents(self, texts: List[str], batch_size: int = 32) -> List[List[float]]:
        """Vektorisiert eine Liste von Textsegmenten (Chunks) in Batches."""
        vectors = self.model.encode(
            texts,
            batch_size=batch_size,
            show_progress_bar=False,
            normalize_embeddings=True
        )
        return vectors.tolist()

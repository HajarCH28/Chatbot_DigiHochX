import logging
import sys
import time
from pathlib import Path

# Projektverzeichnis zum Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ingestion.pipeline import IngestionPipeline
from src.metadata.catalog_manager import CatalogManager
from src.vectorstore.chroma_manager import ChromaManager

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("Indexierung")

def main():
    t0 = time.time()
    logger.info("Starte Indexierungsprozess in ChromaDB...")

    # 1. Ingestion und Segmentierung
    catalog = CatalogManager()
    pipeline = IngestionPipeline(catalog_manager=catalog)
    chunks = pipeline.run(use_cache=True)
    logger.info("Korpus bereit: %d Segmente extrahiert.", len(chunks))

    # 2. Inkrementelle Vektorindexierung (bestehende Chunks bleiben erhalten)
    chroma = ChromaManager()
    existing_doc_ids = chroma.get_existing_doc_ids()
    
    # Nur neue Chunks indexieren (Duplikate werden durch upsert behandelt)
    new_chunks = [c for c in chunks if c.metadata.doc_id not in existing_doc_ids]
    
    if new_chunks:
        indexed_count = chroma.index_chunks(new_chunks)
        logger.info("Neu indexiert: %d Segmente.", indexed_count)
    else:
        # Wenn alle Dokumente schon indexiert sind, trotzdem upsert durchführen
        # für den Fall, dass sich Metadaten geändert haben
        indexed_count = chroma.index_chunks(chunks)
        logger.info("Upsert durchgeführt: %d Segmente aktualisiert.", indexed_count)

    duration = time.time() - t0
    logger.info("Indexierung abgeschlossen: %d Segmente in %.2f Sekunden.", chroma.count(), duration)
    logger.info("Gesamt in ChromaDB-Collection: %d Segmente.", chroma.count())

if __name__ == "__main__":
    main()

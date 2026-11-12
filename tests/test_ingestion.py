import sys
from pathlib import Path
import unittest

# Assurer l'accès au package src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.metadata.catalog_manager import CatalogManager
from src.ingestion.docling_parser import DoclingParser
from src.ingestion.chunker import AcademicChunker
from src.ingestion.pipeline import IngestionPipeline

class TestIngestionPipeline(unittest.TestCase):
    """Vérifie l'ingestion Docling, le catalogue et la fidélité des citations de pages."""

    @classmethod
    def setUpClass(cls):
        cls.catalog = CatalogManager()
        cls.pipeline = IngestionPipeline(catalog_manager=cls.catalog)
        cls.chunks = cls.pipeline.run(use_cache=True)
        cls.stats = cls.pipeline.get_stats(cls.chunks)

    def test_catalog_loaded_all_three_documents(self):
        docs = self.catalog.list_all()
        self.assertEqual(len(docs), 3, "Le catalogue doit contenir exactement 3 documents")
        
        doc_ids = {d.id for d in docs}
        expected_ids = {
            "russ_2025_bita_hochschule",
            "tintore_2013_learning_capacity",
            "elbawab_2024_learning_performance"
        }
        self.assertEqual(doc_ids, expected_ids)

    def test_disciplines_are_assigned(self):
        wi_docs = self.catalog.get_by_discipline("Wirtschaftsinformatik")
        self.assertEqual(len(wi_docs), 1)
        self.assertEqual(wi_docs[0].id, "russ_2025_bita_hochschule")

        org_docs = [d for d in self.catalog.list_all() if "organisationspädagogik" in d.discipline.lower()]
        self.assertEqual(len(org_docs), 2)

    def test_chunks_generated(self):
        self.assertGreater(len(self.chunks), 200, "Le corpus doit produire au moins 200 segments enrichis")

    def test_page_references_present_and_valid(self):
        for chunk in self.chunks:
            meta = chunk.metadata
            self.assertTrue(len(meta.page_numbers) > 0, f"Chunk {chunk.chunk_id} sans numéro de page")
            self.assertTrue(meta.page_display.startswith("p"), f"Citation invalide pour {chunk.chunk_id}: {meta.page_display}")
            self.assertTrue(len(chunk.text.strip()) > 30, f"Chunk trop court : {chunk.chunk_id}")

            # Vérification des bornes de pages physiques
            if meta.doc_id == "russ_2025_bita_hochschule":
                for p in meta.page_numbers:
                    self.assertTrue(1 <= p <= 13, f"Page hors-borne Russ: {p}")
            elif meta.doc_id == "tintore_2013_learning_capacity":
                for p in meta.page_numbers:
                    self.assertTrue(1 <= p <= 19, f"Page hors-borne Tintore: {p}")
            elif meta.doc_id == "elbawab_2024_learning_performance":
                for p in meta.page_numbers:
                    self.assertTrue(1 <= p <= 14, f"Page hors-borne Elbawab: {p}")

    def test_journal_page_formatting(self):
        # Russ et al. doit formater en p. 331 et suivantes
        russ_chunks = [c for c in self.chunks if c.metadata.doc_id == "russ_2025_bita_hochschule"]
        self.assertTrue(any("331" in c.metadata.page_display for c in russ_chunks))
        
        # Tintoré doit formater en p. 375 et suivantes
        tintore_chunks = [c for c in self.chunks if c.metadata.doc_id == "tintore_2013_learning_capacity"]
        self.assertTrue(any("375" in c.metadata.page_display for c in tintore_chunks))

if __name__ == "__main__":
    unittest.main()

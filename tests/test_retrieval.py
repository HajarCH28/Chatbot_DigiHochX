import sys
from pathlib import Path
import unittest

# Assurer l'accès au package src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.vectorstore.chroma_manager import ChromaManager

class TestCrossLingualRetrieval(unittest.TestCase):
    """Vérifie la recherche sémantique multilingue (Allemand <-> Anglais), la traçabilité des pages et les filtres."""

    @classmethod
    def setUpClass(cls):
        cls.chroma = ChromaManager()

    def test_collection_contains_all_chunks(self):
        count = self.chroma.count()
        self.assertEqual(count, 255, f"La collection doit contenir exactement 255 segments, trouvé : {count}")

    def test_german_query_retrieves_english_doc_tintore(self):
        """Requête en Allemand interrogeant un article rédigé en Anglais (Tintoré & Arbós 2013)."""
        query = "Welche internen Barrieren behindern das organisationale Lernen an Hochschulen laut Fragebogen?"
        results = self.chroma.search(query=query, top_k=5)
        
        self.assertGreater(len(results), 0, "La recherche doit renvoyer des résultats")
        
        # Vérifier qu'au moins un des meilleurs résultats provient de Tintoré & Arbós (document en anglais)
        tintore_hits = [r for r in results if r.doc_id == "tintore_2013_learning_capacity"]
        self.assertGreater(len(tintore_hits), 0, "La requête en allemand doit retrouver l'article en anglais de Tintoré")
        
        top_tintore = tintore_hits[0]
        text_lower = top_tintore.text.lower()
        self.assertTrue(
            "learning" in text_lower or "organisation" in text_lower or "questionnaire" in text_lower or "factors" in text_lower
        )
        self.assertTrue(top_tintore.page_display.startswith("p"))
        self.assertGreater(top_tintore.score, 0.50)

    def test_german_query_retrieves_english_doc_elbawab(self):
        """Requête en Allemand interrogeant une étude empirique en Anglais (Elbawab 2024)."""
        query = "Welche Rolle spielen Informationsbeschaffung und Wissenstransfer bei der Hochschulleistung?"
        results = self.chroma.search(query=query, top_k=5)
        
        elbawab_hits = [r for r in results if r.doc_id == "elbawab_2024_learning_performance"]
        self.assertGreater(len(elbawab_hits), 0, "La requête en allemand doit retrouver l'article en anglais d'Elbawab")
        
        top_hit = elbawab_hits[0]
        text_lower = top_hit.text.lower()
        self.assertTrue(
            "information acquisition" in text_lower or "knowledge dissemination" in text_lower or "learning" in text_lower
        )
        self.assertGreater(top_hit.score, 0.45)

    def test_english_query_retrieves_german_doc_russ(self):
        """Requête en Anglais interrogeant un article rédigé en Allemand (Russ et al. 2025)."""
        query = "How did the COVID-19 pandemic affect Business-IT alignment and agile frameworks in the university?"
        results = self.chroma.search(query=query, top_k=5)
        
        russ_hits = [r for r in results if r.doc_id == "russ_2025_bita_hochschule"]
        self.assertGreater(len(russ_hits), 0, "La requête en anglais doit retrouver l'article en allemand de Russ et al.")
        
        top_russ = russ_hits[0]
        self.assertEqual(top_russ.discipline, "Wirtschaftsinformatik")
        self.assertTrue(
            "alignment" in top_russ.text.lower() or "covid" in top_russ.text.lower() or "safe" in top_russ.text.lower()
        )
        self.assertGreater(top_russ.score, 0.45)

    def test_metadata_filtering_by_discipline(self):
        """Filtrage strict par discipline académique (Wirtschaftsinformatik)."""
        query = "Organisationskultur und Führung"
        results = self.chroma.search(
            query=query,
            top_k=5,
            where={"discipline": "Wirtschaftsinformatik"}
        )
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertEqual(r.discipline, "Wirtschaftsinformatik")
            self.assertEqual(r.doc_id, "russ_2025_bita_hochschule")

    def test_metadata_filtering_by_doc_id(self):
        """Filtrage ciblé par identifiant de document."""
        query = "sustainable performance"
        results = self.chroma.search(
            query=query,
            top_k=4,
            where={"doc_id": "elbawab_2024_learning_performance"}
        )
        self.assertGreater(len(results), 0)
        for r in results:
            self.assertEqual(r.doc_id, "elbawab_2024_learning_performance")

if __name__ == "__main__":
    unittest.main()

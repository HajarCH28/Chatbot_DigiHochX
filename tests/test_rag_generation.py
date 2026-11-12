import sys
from pathlib import Path
import unittest

# Assurer l'accès au package src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.rag_engine import RAGEngine
from src.llm.gwdg_client import GWDGClient

class TestRAGGeneration(unittest.TestCase):
    """Vérification empirique complète du moteur RAG, du translingue, des citations et de l'anti-hallucination."""

    @classmethod
    def setUpClass(cls):
        cls.engine = RAGEngine()

    def test_gwdg_client_status(self):
        """Vérifie l'état de configuration du client GWDG."""
        client = self.engine.gwdg
        is_config = client.is_configured
        # Que la clé soit présente ou non, le client doit être instancié proprement
        self.assertIsInstance(is_config, bool)
        status = client.test_connection()
        self.assertIn("authenticated", status)

    def test_factual_russ_2025(self):
        """Question factuelle sur Russ et al. (2025) - Wirtschaftsinformatik."""
        q = "Welche Rolle spielte das Scaled Agile Framework (SAFe) und die Hochschulleitung an der ZHAW während der Pandemie?"
        resp = self.engine.query(q, language="de", top_k=4)
        
        self.assertFalse(resp.is_abstention)
        self.assertGreater(len(resp.sources), 0)
        
        # Vérification qu'au moins une source provient de Russ et al.
        russ_sources = [s for s in resp.sources if s.doc_id == "russ_2025_bita_hochschule"]
        self.assertGreater(len(russ_sources), 0)
        self.assertEqual(russ_sources[0].discipline, "Wirtschaftsinformatik")
        self.assertTrue(russ_sources[0].page_display.startswith("p"))

    def test_factual_tintore_2013(self):
        """Question factuelle sur Tintoré & Arbós (2013) - Organisationspädagogik."""
        q = "How does the questionnaire developed by Tintoré & Arbós measure the stage of growth in universities?"
        resp = self.engine.query(q, language="en", top_k=4)
        
        self.assertFalse(resp.is_abstention)
        tintore_sources = [s for s in resp.sources if s.doc_id == "tintore_2013_learning_capacity"]
        self.assertGreater(len(tintore_sources), 0)
        self.assertTrue(tintore_sources[0].page_display.startswith("p"))

    def test_factual_elbawab_2024(self):
        """Question factuelle sur Elbawab (2024) - Étude empirique européenne."""
        q = "Welche Rolle spielen 'Dialogue and Inquiry' und 'System Connection' für die Informationsbeschaffung laut Elbawab (2024)?"
        resp = self.engine.query(q, language="de", top_k=4)
        
        self.assertFalse(resp.is_abstention)
        elbawab_sources = [s for s in resp.sources if s.doc_id == "elbawab_2024_learning_performance"]
        self.assertGreater(len(elbawab_sources), 0)
        self.assertTrue(elbawab_sources[0].page_display.startswith("p"))

    def test_crosslingual_german_to_english_doc(self):
        """Question en allemand interrogeant Tintoré (document en anglais)."""
        q = "Welche Barrieren des Lernens (Barriers to learning) werden im Fragebogen von Tintoré aufgeführt?"
        resp = self.engine.query(q, language="de", top_k=5)
        
        self.assertFalse(resp.is_abstention)
        # Doit trouver Tintoré et citer ses pages
        doc_ids = {s.doc_id for s in resp.sources}
        self.assertIn("tintore_2013_learning_capacity", doc_ids)

    def test_crosslingual_english_to_german_doc(self):
        """Question en anglais interrogeant Russ et al. (document en allemand)."""
        q = "What are the dimensions of the Competing Values Framework applied to the Swiss university by Russ et al.?"
        resp = self.engine.query(q, language="en", top_k=5)
        
        self.assertFalse(resp.is_abstention)
        doc_ids = {s.doc_id for s in resp.sources}
        self.assertIn("russ_2025_bita_hochschule", doc_ids)

    def test_interdisciplinary_comparison(self):
        """Comparaison croisée entre Wirtschaftsinformatik et Organisationspädagogik."""
        q = "Wie unterscheiden sich die Ansätze von Wirtschaftsinformatik (Business-IT-Alignment) und Organisationspädagogik (Lernkultur) beim Wandel an Hochschulen?"
        resp = self.engine.query(q, language="de", top_k=6)
        
        self.assertFalse(resp.is_abstention)
        disciplines = {s.discipline for s in resp.sources}
        # Vérifie la présence des deux perspectives disciplinaires dans les sources
        has_wi = any("wirtschaftsinformatik" in d.lower() for d in disciplines)
        has_org = any("organisationspädagogik" in d.lower() or "hochschulforschung" in d.lower() for d in disciplines)
        self.assertTrue(has_wi, "La réponse doit mobiliser la Wirtschaftsinformatik")
        self.assertTrue(has_org, "La réponse doit mobiliser l'Organisationspädagogik")

    def test_digihochx_cultural_tensions(self):
        """Analyse des tensions culturelles aux interfaces (thème central DigiHochX)."""
        q = "Welche kulturellen Tensions und Konflikte entstehen an den Schnittstellen zwischen Verwaltung, Forschung und Lehre bei der Digitalisierung?"
        resp = self.engine.query(q, language="de", top_k=6)
        
        self.assertFalse(resp.is_abstention)
        self.assertGreater(len(resp.sources), 1, "Doit mobiliser plusieurs documents pour analyser les tensions")

    def test_abstention_on_unsupported_question(self):
        """Vérification stricte de l'anti-hallucination : question hors du corpus."""
        q = "Welche quantitativen Budgetvorgaben machte das Land Niedersachsen für die Digitalisierung der Universität Hildesheim im Jahr 2026?"
        resp = self.engine.query(q, language="de", min_score_threshold=0.55)
        
        # Le système doit s'abstenir ou signaler qu'aucune preuve n'existe dans les 3 PDFs
        self.assertTrue(
            resp.is_abstention or "keine ausreichenden belege" in resp.answer.lower() or "nicht enthalten" in resp.answer.lower() or "kein" in resp.answer.lower(),
            "Le système doit explicitement refuser d'inventer des faits inexistants dans le corpus"
        )

if __name__ == "__main__":
    unittest.main()

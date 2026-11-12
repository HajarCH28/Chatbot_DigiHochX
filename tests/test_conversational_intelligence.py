"""
Unit- und Integrationstests für die konversationelle Intelligenz und das Intent-Routing.
Testet alle 10 vom Nutzer geforderten Szenarien:
1. Hallo
2. Guten Morgen
3. Danke
4. Wer bist du?
5. Was kannst du?
6. Can you answer in English?
7. Erkläre mir diesen Begriff einfacher.
8. Welche deskriptiven Beiträge finden sich bei Russ et al.?
9. Vergleiche Wirtschaftsinformatik und Organisationspädagogik anhand der Dokumente.
10. Welche Forschungsfragen lassen sich aus den analysierten Quellen ableiten?
"""

import sys
from pathlib import Path
import unittest

# Projektverzeichnis zum Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.rag_engine import RAGEngine
from src.core.intent_classifier import IntentClassifier, UserIntent


class TestConversationalIntelligence(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.engine = RAGEngine()

    # ─────────────────────────────────────────────────────────────────────────
    # TEST CASES 1-7: KONVERSATIONELLER MODUS (OHNE RAG-RETRIEVAL)
    # ─────────────────────────────────────────────────────────────────────────

    def test_01_greeting_hallo(self):
        """1. Hallo -> Sofortige Begrüßung ohne RAG-Suche."""
        q = "Hallo"
        intent_res = IntentClassifier.classify(q)
        self.assertEqual(intent_res.intent, UserIntent.GREETING)
        self.assertTrue(intent_res.is_conversational)

        resp = self.engine.query(q, language="de")
        self.assertTrue(resp.is_conversational)
        self.assertEqual(len(resp.sources), 0, "Darf keine RAG-Quellen für Hallo abrufen")
        self.assertFalse(resp.is_abstention)
        self.assertIn("Willkommen", resp.answer)
        self.assertIn("DigiHochX", resp.answer)

    def test_02_greeting_guten_morgen(self):
        """2. Guten Morgen -> Tageszeit-Begrüßung ohne RAG."""
        q = "Guten Morgen"
        intent_res = IntentClassifier.classify(q)
        self.assertEqual(intent_res.intent, UserIntent.GREETING)
        self.assertTrue(intent_res.is_conversational)

        resp = self.engine.query(q, language="de")
        self.assertTrue(resp.is_conversational)
        self.assertEqual(len(resp.sources), 0)
        self.assertIn("Guten Morgen", resp.answer)

    def test_03_acknowledgement_danke(self):
        """3. Danke -> Höfliche Bestätigung ohne RAG."""
        q = "Danke"
        intent_res = IntentClassifier.classify(q)
        self.assertEqual(intent_res.intent, UserIntent.ACKNOWLEDGEMENT)
        self.assertTrue(intent_res.is_conversational)

        resp = self.engine.query(q, language="de")
        self.assertTrue(resp.is_conversational)
        self.assertEqual(len(resp.sources), 0)
        self.assertTrue("gerne" in resp.answer.lower() or "helfe" in resp.answer.lower())

    def test_04_identity_wer_bist_du(self):
        """4. Wer bist du? -> Klare akademische Identität ohne RAG."""
        q = "Wer bist du?"
        intent_res = IntentClassifier.classify(q)
        self.assertEqual(intent_res.intent, UserIntent.IDENTITY_OR_CAPABILITIES)
        self.assertTrue(intent_res.is_conversational)

        resp = self.engine.query(q, language="de")
        self.assertTrue(resp.is_conversational)
        self.assertEqual(len(resp.sources), 0)
        self.assertIn("DigiHochX", resp.answer)
        self.assertIn("Hildesheim", resp.answer)
        self.assertIn("Knackstedt", resp.answer)

    def test_05_capabilities_was_kannst_du(self):
        """5. Was kannst du? -> Fähigkeitenübersicht ohne RAG."""
        q = "Was kannst du?"
        intent_res = IntentClassifier.classify(q)
        self.assertEqual(intent_res.intent, UserIntent.IDENTITY_OR_CAPABILITIES)
        self.assertTrue(intent_res.is_conversational)

        resp = self.engine.query(q, language="de")
        self.assertTrue(resp.is_conversational)
        self.assertEqual(len(resp.sources), 0)
        self.assertIn("Forschungsagenda", resp.answer)
        self.assertTrue("deskriptiv" in resp.answer.lower() and "präskriptiv" in resp.answer.lower())

    def test_06_language_request_english(self):
        """6. Can you answer in English? -> Sprachwechsel-Bestätigung ohne RAG."""
        q = "Can you answer in English?"
        intent_res = IntentClassifier.classify(q)
        self.assertEqual(intent_res.intent, UserIntent.LANGUAGE_REQUEST)
        self.assertTrue(intent_res.is_conversational)
        self.assertEqual(intent_res.requested_language, "en")

        resp = self.engine.query(q, language="de")
        self.assertTrue(resp.is_conversational)
        self.assertEqual(len(resp.sources), 0)
        self.assertEqual(resp.requested_language, "en")
        self.assertIn("English", resp.answer)

    def test_07_simplification_request(self):
        """7. Erkläre mir diesen Begriff einfacher. -> Natürliche Vereinfachungsanfrage."""
        q = "Erkläre mir diesen Begriff einfacher."
        intent_res = IntentClassifier.classify(q)
        self.assertEqual(intent_res.intent, UserIntent.SIMPLIFICATION_REQUEST)
        self.assertTrue(intent_res.is_conversational)

        # Test mit vorangegangener Nachricht
        fake_history = [
            {"role": "user", "content": "Was ist Business-IT-Alignment?"},
            {"role": "assistant", "content": "Business-IT-Alignment bezeichnet die strategische Passung und Koordination zwischen Unternehmensstrategie und IT-Infrastruktur."}
        ]
        resp = self.engine.query(q, language="de", chat_history=fake_history)
        self.assertTrue(resp.is_conversational)
        self.assertEqual(len(resp.sources), 0)
        self.assertTrue(len(resp.answer) > 50)

    # ─────────────────────────────────────────────────────────────────────────
    # TEST CASES 8-10: WISSENSCHAFTLICHER FORSCHUNGSMODUS (MIT RAG)
    # ─────────────────────────────────────────────────────────────────────────

    def test_08_scientific_russ_descriptive(self):
        """8. Welche deskriptiven Beiträge finden sich bei Russ et al.? -> RAG mit Quellen."""
        q = "Welche deskriptiven Beiträge finden sich bei Russ et al.?"
        intent_res = IntentClassifier.classify(q)
        self.assertFalse(intent_res.is_conversational, "Wissenschaftliche Frage muss RAG auslösen")

        resp = self.engine.query(q, language="de")
        self.assertFalse(resp.is_conversational)
        self.assertGreater(len(resp.sources), 0, "Muss Belege aus Russ et al. liefern")
        russ_sources = [s for s in resp.sources if "russ" in s.doc_id.lower()]
        self.assertGreater(len(russ_sources), 0)
        self.assertTrue(russ_sources[0].page_display.startswith("p") or russ_sources[0].page_display.startswith("S"))

    def test_09_scientific_interdisciplinary_wi_op(self):
        """9. Vergleiche Wirtschaftsinformatik und Organisationspädagogik anhand der Dokumente."""
        q = "Vergleiche Wirtschaftsinformatik und Organisationspädagogik anhand der Dokumente."
        intent_res = IntentClassifier.classify(q)
        self.assertFalse(intent_res.is_conversational)
        self.assertEqual(intent_res.analysis_mode, "interdisciplinary")

        resp = self.engine.query(q, language="de")
        self.assertFalse(resp.is_conversational)
        self.assertGreater(len(resp.sources), 0)
        disciplines = {s.discipline.lower() for s in resp.sources}
        self.assertTrue(any("wirtschaft" in d for d in disciplines))
        self.assertTrue(any("organisations" in d for d in disciplines))

    def test_10_scientific_research_questions(self):
        """10. Welche Forschungsfragen lassen sich aus den analysierten Quellen ableiten?"""
        q = "Welche Forschungsfragen lassen sich aus den analysierten Quellen ableiten?"
        intent_res = IntentClassifier.classify(q)
        self.assertFalse(intent_res.is_conversational)
        self.assertEqual(intent_res.analysis_mode, "research_questions")

        resp = self.engine.query(q, language="de")
        self.assertFalse(resp.is_conversational)
        self.assertGreater(len(resp.sources), 0)
        self.assertFalse(resp.is_abstention)


if __name__ == "__main__":
    unittest.main()


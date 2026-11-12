"""
Automatisierter Validierungstest für die 5 Kernfragen des DigiHochX Chatbots.
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.rag_engine import RAGEngine

def main():
    engine = RAGEngine()

    tests = [
        ("Test 1 (Factual)", "Welche drei Dimensionen der Business-IT-Abstimmung nennen Russ et al. (2025)?"),
        ("Test 2 (Source-specific)", "Welche Rolle übernehmen IT-Einheiten laut Russ et al. (2025)?"),
        ("Test 3 (Descriptive/Prescriptive)", "Welche deskriptiven und präskriptiven Beiträge lassen sich in den indexierten Dokumenten identifizieren?"),
        ("Test 4 (Interdisciplinary)", "Welche Gemeinsamkeiten und Unterschiede zeigen sich zwischen Wirtschaftsinformatik und Organisationspädagogik in den analysierten Dokumenten?"),
        ("Test 5 (Out-of-corpus)", "Was sind die neuesten gesetzlichen Regelungen zur künstlichen Intelligenz in Deutschland?")
    ]

    print("=" * 60)
    print("DIGIHOCHX VALIDATION REPORT - 5 CORE RESEARCH TESTS")
    print("=" * 60)

    for idx, (label, question) in enumerate(tests, 1):
        print(f"\n--- {label} ---")
        print(f"Frage: {question}")
        resp = engine.query(question=question, language="de")
        print(f"Status Abstention: {resp.is_abstention}")
        print(f"Zitierte Quellen: {len(resp.sources)}")
        print(f"Modell: {resp.model_used}")
        print("Auszug Antwort:")
        print(resp.answer[:300].strip())
        print("\nZitationen:")
        for s in resp.sources[:4]:
            print(f"  * {s.short_title}, {s.page_display} (Score: {s.relevance_score})")

if __name__ == "__main__":
    main()

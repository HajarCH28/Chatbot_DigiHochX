"""
Wissenschaftlicher Validierungstest für Phase 5 & 6 (Use Case 3: Forschungsagenda).
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.rag_engine import RAGEngine

def main():
    engine = RAGEngine()

    tests = [
        (
            "Test A: Interdisziplinäre Synthese",
            "Wie unterscheiden sich und ergänzen sich Organisationspädagogik und Wirtschaftsinformatik bei der Analyse von Digitalisierungsprozessen an Hochschulen?",
            "interdisciplinary"
        ),
        (
            "Test B: Forschungslücken",
            "Welche Forschungslücken benennen die Autoren der indexierten Dokumente?",
            "research_gaps"
        ),
        (
            "Test C: Strukturierte Forschungsagenda (Use Case 3)",
            "Erstelle einen strukturierten Entwurf für eine Forschungsagenda zu organisationskulturellen Konflikten an Hochschulen (Use Case 3).",
            "research_agenda"
        )
    ]

    print("=" * 70)
    print("DIGIHOCHX SCIENTIFIC CAPABILITIES VALIDATION (USE CASE 3)")
    print("=" * 70)

    for label, query, mode in tests:
        print(f"\n>>> {label} (Modus: {mode})")
        print(f"Query: {query}")
        resp = engine.query(question=query, analysis_mode=mode, language="de")
        print(f"Modell: {resp.model_used} | Abstention: {resp.is_abstention} | Quellen: {len(resp.sources)}")
        print("Antwortauszug (erste 450 Zeichen):")
        print(resp.answer[:450].replace("\n", " "))
        print("Zitierte Quellen:")
        for s in resp.sources[:4]:
            print(f"  * {s.short_title}, {s.page_display} (Score: {s.relevance_score})")

if __name__ == "__main__":
    main()


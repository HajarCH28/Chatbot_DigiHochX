import sys
from pathlib import Path
import json

# Assurer l'accès au package src
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.core.rag_engine import RAGEngine

TEST_QUESTIONS = [
    {
        "id": "q1_factual_wi",
        "category": "Faktenfrage Wirtschaftsinformatik (Russ et al. 2025)",
        "language": "de",
        "question": "Welche Merkmale kennzeichnen die ICT-Organisation der ZHAW und welche Rolle spielte das agile Framework SAFe während der COVID-19-Pandemie?"
    },
    {
        "id": "q2_factual_orgpaed",
        "category": "Faktenfrage Organisationspädagogik (Tintoré & Arbós 2013)",
        "language": "de",
        "question": "Welche internen Barrieren des organisationalen Lernens identifizieren Tintoré & Arbós in ihrem Fragebogenmodell?"
    },
    {
        "id": "q3_factual_empirical",
        "category": "Faktenfrage Empirische Hochschulforschung (Elbawab 2024)",
        "language": "de",
        "question": "Wie beeinflussen die Prozesse 'Information Acquisition' und 'Knowledge Dissemination' die Hochschulleistung laut Elbawab (2024)?"
    },
    {
        "id": "q4_crosslingual_en_de",
        "category": "Translinguale Frage EN -> DE (Russ et al. 2025)",
        "language": "en",
        "question": "How did the leadership role and coordination between university management and ICT change after the COVID-19 pandemic according to Russ et al.?"
    },
    {
        "id": "q5_interdisciplinary",
        "category": "Interdisziplinärer Vergleich (WI vs. OrgPäd)",
        "language": "de",
        "question": "Inwiefern unterscheidet sich der Blickwinkel der Wirtschaftsinformatik (Business-IT-Alignment) von jenem der Organisationspädagogik (Lernkultur) bei der Transformation von Hochschulen?"
    },
    {
        "id": "q6_digihochx_tensions",
        "category": "Kulturelle Tensions DigiHochX (Verwaltung / Forschung / Lehre)",
        "language": "de",
        "question": "Welche Spannungen und Konflikte entstehen an den Schnittstellen zwischen Verwaltung, Forschung und Lehre durch Digitalisierungsmaßnahmen?"
    },
    {
        "id": "q7_abstention",
        "category": "Abstentions- / Anti-Halluzinationstest (Hors-Corpus)",
        "language": "de",
        "question": "Welche genauen Fördersummen und Fristen wurden vom Land Niedersachsen für das Digitalpaket 2026 der Universität Hildesheim beschlossen?"
    }
]

def run_evaluation():
    engine = RAGEngine()
    print("================================================================================")
    print("DIGIHOCHX - EVALUATION DER MODELLARCHITEKTUR & TESTFRAGEN")
    print("================================================================================")
    print(f"GWDG API Authentifiziert : {engine.gwdg.is_configured}")
    print(f"Modellstandard           : {engine.gwdg.default_model}")
    print("Corpus-Status            : 255 Chunks in ChromaDB (sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2)\n")

    for t in TEST_QUESTIONS:
        print(f"\n--- [{t['id'].upper()}] {t['category']} ---")
        print(f"Frage ({t['language']}): {t['question']}")
        
        # Exécution via le moteur RAG
        resp = engine.query(t["question"], language=t["language"], top_k=4)
        
        print(f"Abstention déclenchée : {resp.is_abstention}")
        print(f"Modèle exécutant      : {resp.model_used}")
        print(f"Sources citées ({len(resp.sources)}) :")
        for s in resp.sources:
            print(f"  * [{s.short_title}, {s.page_display}] ({s.discipline}) - Score: {s.relevance_score}")
        print(f"Aperçu réponse :\n{resp.answer[:300]}...\n")

if __name__ == "__main__":
    run_evaluation()

import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.core.rag_engine import RAGEngine
from tests.compare_models import TEST_QUESTIONS

REPORT_DIR = BASE_DIR / "tests" / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

def evaluate_citation_fidelity(answer: str, sources: list) -> Dict[str, Any]:
    """Vérifie si les citations mentionnées dans le texte correspondent aux sources et pages réelles."""
    checks = {
        "has_bracketed_citations": "[" in answer and "]" in answer,
        "cited_pages_match_retrieved": False,
        "sources_count": len(sources)
    }
    
    # Vérification de présence des numéros de pages réels dans le texte
    for s in sources:
        if hasattr(s, "page_display") and (s.page_display in answer or str(s.page_numbers[0]) in answer):
            checks["cited_pages_match_retrieved"] = True
            break
            
    return checks

def run_evaluation(models_to_test: List[str] = None):
    engine = RAGEngine()
    is_live = engine.gwdg.is_configured
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    report_file = REPORT_DIR / f"api_evaluation_{timestamp}.json"

    print("=" * 80)
    print("CAMPAGNE D'EVALUATION SCIENTIFIQUE DIGIHOCHX")
    print(f"Mode d'execution : {'API GWDG EN DIRECT (REEL)' if is_live else 'SYNTHESE LOCALE HORS-LIGNE (FALLBACK)'}")
    print(f"Modele par defaut : {engine.gwdg.default_model}")
    print("=" * 80)

    if not is_live:
        print("[AVERTISSEMENT METHODOLOGIQUE]")
        print("Aucune cle API n'etant configuree dans .env, ce test s'execute en mode fallback local.")
        print("Aucun score de performance ne sera attribue a un modele GWDG distant.")
        print("Pour evaluer les vrais modeles GWDG, configurez GWDG_API_KEY dans votre fichier .env.\n")

    models = models_to_test or ([engine.gwdg.default_model] if is_live else ["local_grounded_fallback"])
    all_results = []

    for model_id in models:
        print(f"\n>>> TEST DU MODELE : {model_id} <<<")
        model_results = {
            "model_id": model_id,
            "is_live_api": is_live,
            "test_runs": []
        }

        for q in TEST_QUESTIONS:
            q_id = q["id"]
            question_text = q["question"]
            lang = q["language"]

            print(f"  - Exécution [{q_id}] ({lang}) ...", end="", flush=True)
            t0 = time.time()
            
            try:
                resp = engine.query(question_text, language=lang, top_k=4, model=model_id if is_live else None)
                latency = round(time.time() - t0, 2)
                
                citation_check = evaluate_citation_fidelity(resp.answer, resp.sources)
                
                run_data = {
                    "question_id": q_id,
                    "category": q["category"],
                    "language": lang,
                    "question": question_text,
                    "model_used": resp.model_used,
                    "latency_seconds": latency,
                    "is_abstention": resp.is_abstention,
                    "sources_count": len(resp.sources),
                    "sources": [
                        {
                            "short_title": s.short_title,
                            "page_display": s.page_display,
                            "discipline": s.discipline,
                            "score": s.relevance_score
                        }
                        for s in resp.sources
                    ],
                    "citation_fidelity": citation_check,
                    "raw_answer": resp.answer
                }
                model_results["test_runs"].append(run_data)
                print(f" OK ({latency}s | {len(resp.sources)} sources | Abstention={resp.is_abstention})")
            except Exception as e:
                print(f" ERREUR : {e}")
                model_results["test_runs"].append({
                    "question_id": q_id,
                    "error": str(e)
                })

        all_results.append(model_results)

    # Sauvegarde du rapport JSON complet
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(all_results, f, indent=2, ensure_ascii=False)

    print(f"\nRapport detaille enregistre dans : {report_file}")
    return all_results

if __name__ == "__main__":
    run_evaluation()

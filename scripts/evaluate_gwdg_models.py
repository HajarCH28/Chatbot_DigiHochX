import os
import sys
import json
import time
from pathlib import Path
from typing import List, Dict, Any

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from src.core.rag_engine import RAGEngine
from src.llm.prompts import (
    SYSTEM_PROMPT_DE,
    SYSTEM_PROMPT_EN,
    build_user_prompt,
    format_context_prompt
)
from tests.compare_models import TEST_QUESTIONS

REPORT_DIR = BASE_DIR / "tests" / "reports"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

CANDIDATE_MODELS = [
    "deepseek-v4.1-flash-1017",
    "deepseek-v4-flash-0731",
    "mistral-large-4-1t-a52b"
]

def check_citations(answer: str, retrieved_sources: List[Any]) -> Dict[str, Any]:
    """Analyse la fidélité et la précision des citations générées."""
    cited_docs = []
    cited_pages = []
    
    # Vérification des Kurztitel
    for s in retrieved_sources:
        if s.short_title in answer or s.doc_id in answer:
            cited_docs.append(s.short_title)
        # Vérification des pages citées
        page_ref = s.page_display
        first_p = str(s.page_numbers[0]) if s.page_numbers else ""
        if page_ref in answer or (first_p and f"S. {first_p}" in answer) or (first_p and f"p. {first_p}" in answer):
            cited_pages.append(page_ref)

    return {
        "has_bracket_citations": "[" in answer and "]" in answer,
        "matched_sources": list(set(cited_docs)),
        "matched_pages": list(set(cited_pages)),
        "citation_count": len(set(cited_pages))
    }

def check_abstention(answer: str) -> bool:
    """Détecte si le modèle a refusé de spéculer sur une question hors-corpus."""
    markers = [
        "keine ausreichenden belege",
        "keine belege",
        "nicht enthalten",
        "nicht thematisiert",
        "insufficient evidence",
        "no evidence",
        "unsupported",
        "nicht belegt"
    ]
    return any(m in answer.lower() for m in markers)

def main():
    engine = RAGEngine()
    
    if not engine.gwdg.is_configured:
        print("[FEHLER] GWDG_API_KEY ist nicht in .env konfiguriert. Abbruch.")
        sys.exit(1)

    timestamp = time.strftime("%Y%m%d_%H%M%S")
    json_report_path = REPORT_DIR / f"gwdg_evaluation_{timestamp}.json"
    md_report_path = REPORT_DIR / f"gwdg_evaluation_{timestamp}.md"

    print("=" * 85)
    print("DIGIHOCHX - VERGLEICHENDE EVALUATION DER ECHTEN GWDG-API-MODELLE")
    print(f"Zeitstempel        : {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Endpunkt           : {engine.gwdg.api_base}")
    print(f"Getestete Modelle  : {', '.join(CANDIDATE_MODELS)}")
    print(f"Anzahl Testfragen  : {len(TEST_QUESTIONS)}")
    print("=" * 85)

    # 1. Gemeinsames Retrieval durchführen (exakt identischer Kontext für alle Modelle)
    print("\n>>> SCHRITT 1: Vektor-Retrieval (ChromaDB) für alle 7 Fragen durchführen...")
    question_contexts = {}
    for q in TEST_QUESTIONS:
        q_id = q["id"]
        q_text = q["question"]
        lang = q["language"]
        
        # Abruf der Top-4 Chunks
        raw_results = engine.chroma.search(query=q_text, top_k=4)
        citations = engine._extract_citations(raw_results)
        context_str = format_context_prompt(raw_results)
        user_prompt = build_user_prompt(q_text, context_str, language=lang)
        system_prompt = SYSTEM_PROMPT_EN if lang.lower() == "en" else SYSTEM_PROMPT_DE

        question_contexts[q_id] = {
            "question": q,
            "raw_results": raw_results,
            "citations": citations,
            "context_str": context_str,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        print(f"  * [{q_id}] Kontext aufgebaut: {len(raw_results)} Segmente abgerufen.")

    # 2. Testen aller Modelle gegen exakt dieselben Kontexte
    evaluation_data: Dict[str, Any] = {
        "metadata": {
            "timestamp": timestamp,
            "api_base": engine.gwdg.api_base,
            "models_tested": CANDIDATE_MODELS,
            "total_questions": len(TEST_QUESTIONS)
        },
        "models": {}
    }

    for model_id in CANDIDATE_MODELS:
        print(f"\n" + "-" * 85)
        print(f">>> TESTE MODELL: {model_id} <<<")
        print("-" * 85)
        
        model_runs = []
        for q in TEST_QUESTIONS:
            q_id = q["id"]
            q_meta = question_contexts[q_id]
            messages = q_meta["messages"]
            citations = q_meta["citations"]
            
            print(f"  [{q_id}] Sende Anfrage an GWDG-API ... ", end="", flush=True)
            t0 = time.time()
            error_msg = None
            answer_text = ""
            status_code = 200

            try:
                answer_text = engine.gwdg.generate(
                    messages=messages,
                    model=model_id,
                    temperature=0.2,
                    max_tokens=1500
                )
                latency = round(time.time() - t0, 2)
                print(f"OK ({latency}s)")
            except Exception as e:
                latency = round(time.time() - t0, 2)
                error_msg = str(e)
                status_code = 500
                print(f"FEHLER ({latency}s): {e}")

            # Auswertung der Antwort
            citation_eval = check_citations(answer_text, citations)
            is_abstention = check_abstention(answer_text)

            run_entry = {
                "question_id": q_id,
                "category": q["category"],
                "question": q["question"],
                "language": q["language"],
                "status_code": status_code,
                "latency_seconds": latency,
                "error": error_msg,
                "answer": answer_text,
                "citations_eval": citation_eval,
                "is_abstention": is_abstention,
                "retrieved_sources": [
                    {
                        "short_title": s.short_title,
                        "page_display": s.page_display,
                        "discipline": s.discipline,
                        "score": s.relevance_score
                    }
                    for s in citations
                ]
            }
            model_runs.append(run_entry)

        evaluation_data["models"][model_id] = model_runs

    # 3. Speichern der Rohdaten
    with open(json_report_path, "w", encoding="utf-8") as f:
        json.dump(evaluation_data, f, indent=2, ensure_ascii=False)
    print(f"\n[SPEICHERUNG] Rohdaten erfolgreich gesichert: {json_report_path}")

    # 4. Generierung des Markdown-Vergleichsberichts
    generate_markdown_report(evaluation_data, md_report_path)
    print(f"[SPEICHERUNG] Markdown-Bericht generiert: {md_report_path}")

def generate_markdown_report(data: Dict[str, Any], output_path: Path):
    lines = []
    lines.append("# GWDG Academic Cloud - Vergleichender Evaluationsbericht (Empirische API-Daten)")
    lines.append(f"**Datum:** {data['metadata']['timestamp']} | **Endpunkt:** `{data['metadata']['api_base']}`\n")
    lines.append("## 1. Übersicht der Testergebnisse\n")
    lines.append("| Modell | Erfolgreiche Anfragen | Durchschn. Latenz | Abstention Q7 korrekt | Zitierte Belege (Summe) |")
    lines.append("| :--- | :---: | :---: | :---: | :---: |")

    for model_id, runs in data["models"].items():
        success_count = sum(1 for r in runs if not r["error"])
        avg_latency = sum(r["latency_seconds"] for r in runs) / len(runs) if runs else 0
        q7_run = next((r for r in runs if r["question_id"] == "q7_abstention"), None)
        q7_ok = q7_run and q7_run["is_abstention"]
        total_citations = sum(r["citations_eval"]["citation_count"] for r in runs)
        
        lines.append(f"| **`{model_id}`** | {success_count}/{len(runs)} | {avg_latency:.2f}s | {'Ja (Erfolgreich)' if q7_ok else 'Nein (Halluzination/Unsicher)'} | {total_citations} Fundstellen |")

    lines.append("\n## 2. Detaillierte Analyse pro Testfrage\n")

    for q_idx, q in enumerate(TEST_QUESTIONS):
        q_id = q["id"]
        lines.append(f"### Frage {q_idx+1}: {q['category']}")
        lines.append(f"**Fragetext ({q['language']}):** *{q['question']}*\n")
        
        for model_id, runs in data["models"].items():
            run = next(r for r in runs if r["question_id"] == q_id)
            lines.append(f"#### Modell: `{model_id}` (Latenz: {run['latency_seconds']}s | HTTP: {run['status_code']})")
            if run["error"]:
                lines.append(f"> **Fehler:** {run['error']}\n")
            else:
                lines.append(f"> {run['answer']}\n")
                lines.append(f"*Erkannte Zitationsbelege:* `{run['citations_eval']['matched_pages']}` | *Abstention:* `{run['is_abstention']}`\n")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

if __name__ == "__main__":
    main()

import logging
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from src.vectorstore.chroma_manager import ChromaManager, SearchResult
from src.llm.gwdg_client import GWDGClient, GWDGAuthenticationError
from src.llm.prompts import (
    SYSTEM_PROMPT_DE,
    SYSTEM_PROMPT_EN,
    build_user_prompt,
    format_context_prompt
)
from src.core.intent_classifier import IntentClassifier, IntentResult, UserIntent
from src.core.conversation_handler import ConversationHandler

logger = logging.getLogger(__name__)

class SourceCitation(BaseModel):
    """Verifizierte bibliographische Referenz zu einer Antwort."""
    doc_id: str
    short_title: str
    authors: str
    year: int
    discipline: str
    research_type: str = ""
    page_display: str
    page_numbers: List[int]
    relevance_score: float

class RAGResponse(BaseModel):
    """Strukturierte und nachvollziehbare Forschungsantwort."""
    question: str
    answer: str
    language: str
    sources: List[SourceCitation]
    retrieved_chunks: List[SearchResult]
    is_abstention: bool = Field(default=False, description="Wahr, wenn das System mangels Belegen im Korpus abstinent ist")
    model_used: str
    analysis_mode: str = "general"
    intent: str = "scientific_question"
    is_conversational: bool = False
    requested_language: Optional[str] = None

class RAGEngine:
    """Akademischer RAG-Motor für DigiHochX mit integrierter Konversationsintelligenz."""

    def __init__(
        self,
        chroma_manager: Optional[ChromaManager] = None,
        gwdg_client: Optional[GWDGClient] = None
    ):
        self.chroma = chroma_manager or ChromaManager()
        self.gwdg = gwdg_client or GWDGClient()

    def _extract_citations(self, chunks: List[SearchResult]) -> List[SourceCitation]:
        """Extrahiert eine deduplizierte und sortierte Liste der zitierten Quellen."""
        seen = set()
        citations = []
        for c in chunks:
            key = (c.doc_id, c.page_display)
            if key not in seen:
                seen.add(key)
                citations.append(SourceCitation(
                    doc_id=c.doc_id,
                    short_title=c.short_title,
                    authors=c.authors,
                    year=c.year,
                    discipline=c.discipline,
                    research_type=getattr(c, 'research_type', ''),
                    page_display=c.page_display,
                    page_numbers=c.page_numbers,
                    relevance_score=c.score
                ))
        return citations

    def _generate_grounded_fallback_summary(
        self,
        question: str,
        chunks: List[SearchResult],
        language: str = "de",
        offline_reason: Optional[str] = None
    ) -> str:
        """Deterministischer Offline-Synthesizer, wenn kein GWDG-API-Schlüssel aktiv oder der Dienst nicht erreichbar ist."""
        if not chunks:
            if language == "en":
                return "The provided documents do not contain sufficient evidence to answer this question."
            return "Zu dieser Fragestellung enthalten die bereitgestellten Dokumente keine ausreichenden Belege."

        lines = []
        if language == "en":
            lines.append("### Synthesized Research Findings (Offline Grounded Mode)\n")
            note = offline_reason or ("GWDG API key not configured." if not self.gwdg.is_configured else "GWDG API service temporarily unreachable.")
            lines.append(f"*Note: {note} Directly synthesizing factual evidence from {len(chunks)} relevant excerpts:*\n")
            for idx, c in enumerate(chunks, 1):
                clean_snippet = c.text[:280].replace("\n", " ").strip()
                rt_tag = f" [{c.research_type}]" if c.research_type else ""
                lines.append(f"**{idx}. [{c.short_title}, {c.page_display}]** ({c.discipline}{rt_tag}):")
                lines.append(f'> "{clean_snippet}..."\n')
        else:
            lines.append("### Wissenschaftliche Befundsynthese (Lokaler Grounding-Modus)\n")
            note = offline_reason or ("Kein GWDG-API-Schlüssel konfiguriert." if not self.gwdg.is_configured else "GWDG-Dienst vorübergehend nicht erreichbar.")
            lines.append(f"*Hinweis: {note} Direkte quellenbasierte Synthese aus {len(chunks)} relevanten Textabschnitten:*\n")
            for idx, c in enumerate(chunks, 1):
                clean_snippet = c.text[:280].replace("\n", " ").strip()
                rt_tag = f" [{c.research_type}]" if c.research_type else ""
                lines.append(f"**{idx}. [{c.short_title}, {c.page_display}]** ({c.discipline}{rt_tag}):")
                lines.append(f'> "{clean_snippet}..."\n')

        return "\n".join(lines)

    def query(
        self,
        question: str,
        language: str = "de",
        top_k: int = 8,
        discipline_filter: Optional[str] = None,
        doc_id_filter: Optional[str] = None,
        research_type_filter: Optional[str] = None,
        min_score_threshold: float = 0.25,
        model: Optional[str] = None,
        analysis_mode: str = "general",
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> RAGResponse:
        """Führt eine intelligente Klassifikation durch und routet zwischen Dialogmodus und wissenschaftlichem RAG."""
        
        # 1. Intent-Klassifikation vor jeglichem Vektordatenbank-Aufruf
        intent_result = IntentClassifier.classify(question, current_language=language)
        eff_lang = intent_result.requested_language or language

        # 2. Reiner Konversationsmodus: KEIN ChromaDB-Retrieval
        if intent_result.is_conversational:
            answer = ConversationHandler.respond(
                intent_result=intent_result,
                user_query=question,
                language=eff_lang,
                chat_history=chat_history,
                gwdg_client=self.gwdg,
                model=model or self.gwdg.default_model
            )
            return RAGResponse(
                question=question,
                answer=answer,
                language=eff_lang,
                sources=[],
                retrieved_chunks=[],
                is_abstention=False,
                model_used="Conversational Intelligence",
                analysis_mode="conversational",
                intent=intent_result.intent.value,
                is_conversational=True,
                requested_language=intent_result.requested_language
            )

        # 3. Wissenschaftlicher RAG-Modus: Analysemodus automatisch verfeinern
        effective_mode = analysis_mode if analysis_mode != "general" else intent_result.analysis_mode

        # 4. Autor-/Dokumenten-spezifische Signalerkennung für präzises Hybrid-Retrieval
        author_doc_mapping = {
            "russ": "russ_2025_bita_hochschule",
            "sieber": "russ_2025_bita_hochschule",
            "weber": "russ_2025_bita_hochschule",
            "leikert": "russ_2025_bita_hochschule",
            "tintore": "tintore_2013_learning_capacity",
            "tintoré": "tintore_2013_learning_capacity",
            "arbo": "tintore_2013_learning_capacity",
            "arbós": "tintore_2013_learning_capacity",
            "elbawab": "elbawab_2024_learning_performance",
        }
        detected_doc_id = doc_id_filter
        if not detected_doc_id:
            q_lower = question.lower()
            for author_key, target_doc in author_doc_mapping.items():
                if author_key in q_lower:
                    detected_doc_id = target_doc
                    break

        # 5. ChromaDB-Filter vorbereiten
        where_conditions = []
        if discipline_filter:
            where_conditions.append({"discipline": discipline_filter})
        if doc_id_filter:
            where_conditions.append({"doc_id": doc_id_filter})
        if research_type_filter:
            where_conditions.append({"research_type": research_type_filter})

        where_filter = None
        if len(where_conditions) == 1:
            where_filter = where_conditions[0]
        elif len(where_conditions) > 1:
            where_filter = {"$and": where_conditions}

        # 6. Semantische Vektorsuche (Hybrid aus Autor-Fokus und globaler Suche)
        raw_results = self.chroma.search(
            query=question,
            top_k=top_k,
            where=where_filter
        )

        # Falls ein spezifischer Autor/Dokument in der Frage genannt wurde und kein Filter aktiv war:
        # Zusätzliche fokussierte Suche im Zieldokument durchführen und Ergebnisse dedupliziert vereinen
        if detected_doc_id and not doc_id_filter:
            doc_specific_results = self.chroma.search(
                query=question,
                top_k=max(top_k, 12),
                where={"doc_id": detected_doc_id}
            )
            seen_cids = {r.chunk_id for r in raw_results}
            for dr in doc_specific_results:
                if dr.chunk_id not in seen_cids:
                    raw_results.append(dr)
                    seen_cids.add(dr.chunk_id)

        # 7. Sibling Context Expansion: Unvollständige Aufzählungen & Folgesegmente verknüpfen
        needed_siblings = []
        seen_all_cids = {r.chunk_id for r in raw_results}
        for r in raw_results:
            cid = r.chunk_id
            if "_c" in cid:
                parts = cid.rsplit("_c", 1)
                if len(parts) == 2 and parts[1].isdigit():
                    curr_idx = int(parts[1])
                    # Vorherigen Chunk prüfen, wenn der Text mitten in einer Aufzählung beginnt (z.B. "4. ", "3. ")
                    prev_cid = f"{parts[0]}_c{curr_idx - 1:03d}"
                    clean_start = r.text.lstrip()
                    if any(clean_start.startswith(f"{n}.") for n in range(2, 10)) and prev_cid not in seen_all_cids and curr_idx > 0:
                        needed_siblings.append(prev_cid)
                        seen_all_cids.add(prev_cid)

                    # Nächsten Chunk prüfen, wenn der Text mit ':' endet oder eine Aufzählung ankündigt
                    next_cid = f"{parts[0]}_c{curr_idx + 1:03d}"
                    if r.text.rstrip().endswith(":") and next_cid not in seen_all_cids:
                        needed_siblings.append(next_cid)
                        seen_all_cids.add(next_cid)

        if needed_siblings:
            sibling_chunks = self.chroma.get_chunks_by_ids(needed_siblings)
            raw_results.extend(sibling_chunks)

        # 8. Semantisches Rauschen filtern (< Schwellenwert)
        valid_chunks = [r for r in raw_results if r.score >= min_score_threshold]
        
        # Wenn kein Chunk den minimalen Schwellenwert überschreitet
        if not valid_chunks:
            abstention_msg = (
                "The provided documents do not contain sufficient evidence to answer this question."
                if eff_lang.lower() == "en"
                else "Zu dieser Fragestellung enthalten die bereitgestellten Dokumente keine ausreichenden Belege."
            )
            return RAGResponse(
                question=question,
                answer=abstention_msg,
                language=eff_lang,
                sources=[],
                retrieved_chunks=raw_results,
                is_abstention=True,
                model_used="GroundingGuard (No Context)",
                analysis_mode=effective_mode,
                intent=intent_result.intent.value,
                is_conversational=False
            )

        # 9. Wissenschaftlichen Kontext und Zitate formatieren
        context_str = format_context_prompt(valid_chunks)
        user_content = build_user_prompt(question, context_str, language=eff_lang, analysis_mode=effective_mode)
        system_content = SYSTEM_PROMPT_EN if eff_lang.lower() == "en" else SYSTEM_PROMPT_DE

        messages = [
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_content}
        ]

        # 10. GWDG-LLM aufrufen oder auf deterministischen Synthesizer zurückfallen
        citations = self._extract_citations(valid_chunks)
        target_model = model or self.gwdg.default_model

        if self.gwdg.is_configured:
            try:
                answer = self.gwdg.generate(messages=messages, model=target_model)
                model_name = target_model
            except Exception as e:
                logger.warning("GWDG-LLM-Aufruf fehlgeschlagen: %s. Lokale Synthese wird verwendet.", e)
                answer = self._generate_grounded_fallback_summary(
                    question, valid_chunks, language=eff_lang,
                    offline_reason=f"GWDG-Dienst nicht erreichbar ({type(e).__name__})"
                )
                model_name = f"Fallback ({type(e).__name__})"
        else:
            answer = self._generate_grounded_fallback_summary(
                question, valid_chunks, language=eff_lang,
                offline_reason="Kein GWDG-API-Schlüssel konfiguriert"
            )
            model_name = f"Local Grounded Synthesizer ({target_model})"

        # 11. Echte wissenschaftliche Abstention erkennen
        ans_lower = answer.strip().lower()
        refusal_phrases = [
            "zu dieser fragestellung enthalten die bereitgestellten dokumente keine ausreichenden belege",
            "the provided documents do not contain sufficient evidence",
            "keine belege in den bereitgestellten dokumenten",
            "keiner der übergebenen textauszüge",
            "keiner der bereitgestellten textauszüge",
            "enthalten keine belege zu dieser fragestellung"
        ]
        is_abstention = any(phrase in ans_lower[:300] for phrase in refusal_phrases)

        # Quellenbelege leeren, wenn mangels Belegen abstiniert wird
        should_retain_sources = not is_abstention and len(valid_chunks) > 0

        return RAGResponse(
            question=question,
            answer=answer,
            language=eff_lang,
            sources=citations if should_retain_sources else [],
            retrieved_chunks=valid_chunks,
            is_abstention=is_abstention,
            model_used=model_name,
            analysis_mode=effective_mode,
            intent=intent_result.intent.value,
            is_conversational=False
        )

    def get_corpus_stats(self) -> Dict[str, Any]:
        """Gibt Statistiken über den indexierten Korpus zurück."""
        count = self.chroma.count()
        # Alle Chunks abrufen für Statistiken
        try:
            collection_data = self.chroma.collection.get(include=["metadatas"])
            metadatas = collection_data.get("metadatas", [])

            docs = {}
            disciplines = {}
            research_types = {}

            for meta in metadatas:
                doc_id = meta.get("doc_id", "unknown")
                disc = meta.get("discipline", "unknown")
                rt = meta.get("research_type", "unknown")

                if doc_id not in docs:
                    docs[doc_id] = {
                        "short_title": meta.get("short_title", ""),
                        "authors": meta.get("authors", ""),
                        "year": meta.get("year", 0),
                        "discipline": disc,
                        "research_type": rt,
                        "chunk_count": 0
                    }
                docs[doc_id]["chunk_count"] += 1
                disciplines[disc] = disciplines.get(disc, 0) + 1
                research_types[rt] = research_types.get(rt, 0) + 1

            return {
                "total_chunks": count,
                "documents": docs,
                "by_discipline": disciplines,
                "by_research_type": research_types
            }
        except Exception as e:
            logger.warning("Fehler beim Abrufen der Korpus-Statistiken: %s", e)
            return {"total_chunks": count, "documents": {}, "by_discipline": {}, "by_research_type": {}}

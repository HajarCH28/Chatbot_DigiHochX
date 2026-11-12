import re
from typing import List, Set
from docling.chunking import HierarchicalChunker
from docling_core.types.doc import DoclingDocument

from src.ingestion.models import ChunkMetadata, DocumentMetadata, TextChunk

class AcademicChunker:
    """Zerlegt ein DoclingDocument in Segmente, angereichert mit wissenschaftlichen Metadaten und exakten Seitenzahlen."""

    def __init__(self, min_chunk_chars: int = 160, max_chunk_chars: int = 2200):
        self.min_chunk_chars = min_chunk_chars
        self.max_chunk_chars = max_chunk_chars
        self.chunker = HierarchicalChunker()

    def _calculate_journal_page(self, pdf_page: int, metadata: DocumentMetadata) -> int:
        """Berechnet die tatsächliche Zeitschriftenseite, wenn das Dokument ab einer bestimmten Seitennummer beginnt."""
        # Fall Russ et al. (HMD Praxis der Wirtschaftsinformatik 62:331–343)
        if "331" in metadata.publication:
            return 330 + pdf_page
        # Fall Tintoré & Arbós (RUSC pp. 375-393)
        elif "375" in metadata.publication:
            return 374 + pdf_page
        # Fall Elbawab (Humanities & Social Sciences Communications 1-14)
        return pdf_page

    def _format_page_display(self, pdf_pages: List[int], metadata: DocumentMetadata) -> str:
        """Formatiert die akademische Zitatanzeige (z. B. 'S. 333' oder 'pp. 378-379')."""
        if not pdf_pages:
            return "p. N/A"

        journal_pages = [self._calculate_journal_page(p, metadata) for p in sorted(pdf_pages)]
        
        if len(journal_pages) == 1:
            return f"p. {journal_pages[0]}"
        elif len(journal_pages) > 1 and journal_pages[-1] == journal_pages[0] + len(journal_pages) - 1:
            return f"pp. {journal_pages[0]}-{journal_pages[-1]}"
        else:
            return f"pp. {', '.join(map(str, journal_pages))}"

    def chunk_document(self, doc: DoclingDocument, metadata: DocumentMetadata) -> List[TextChunk]:
        """Führt hierarchisches Chunking durch und fusioniert isolierte Mikrosegmente."""
        raw_chunks = list(self.chunker.chunk(doc))
        
        preprocessed_chunks = []
        for idx, rc in enumerate(raw_chunks):
            text = rc.text.strip()
            if not text:
                continue

            # Seitenextraktion über die Provenienz der Dokumentelemente
            pages: Set[int] = set()
            for item in getattr(rc.meta, "doc_items", []):
                for prov in getattr(item, "prov", []):
                    if hasattr(prov, "page_no"):
                        pages.add(prov.page_no)

            raw_headings = getattr(rc.meta, "headings", None)
            headings = [str(h) for h in raw_headings if h] if raw_headings else []
            preprocessed_chunks.append({
                "text": text,
                "pages": sorted(list(pages)) if pages else [1],
                "headings": headings
            })

        # Robuste Fusion durch Akkumulation: kein Fragment bleibt verwaist oder unter dem Schwellenwert
        merged_chunks = []
        accumulator = None

        for item in preprocessed_chunks:
            if accumulator is None:
                accumulator = dict(item)
                continue

            # Wenn der Akkumulator unter dem Schwellenwert liegt ODER das eingehende Element zu klein ist
            if len(accumulator["text"]) < self.min_chunk_chars or len(item["text"]) < 100:
                accumulator["text"] = f"{accumulator['text']}\n{item['text']}".strip()
                accumulator["pages"] = sorted(list(set(accumulator["pages"] + item["pages"])))
                if not accumulator["headings"] and item["headings"]:
                    accumulator["headings"] = item["headings"]
            else:
                merged_chunks.append(accumulator)
                accumulator = dict(item)

        # Letztes akkumuliertes Fragment verarbeiten
        if accumulator:
            if merged_chunks and len(accumulator["text"]) < self.min_chunk_chars:
                merged_chunks[-1]["text"] = f"{merged_chunks[-1]['text']}\n{accumulator['text']}".strip()
                merged_chunks[-1]["pages"] = sorted(list(set(merged_chunks[-1]["pages"] + accumulator["pages"])))
            else:
                merged_chunks.append(accumulator)

        # Finale Pydantic-Objekte erstellen
        authors_formatted = ", ".join(metadata.authors)
        final_chunks: List[TextChunk] = []

        for c_idx, mc in enumerate(merged_chunks, 1):
            chunk_id = f"{metadata.id}_c{c_idx:03d}"
            page_display = self._format_page_display(mc["pages"], metadata)

            chunk_meta = ChunkMetadata(
                doc_id=metadata.id,
                doc_title=metadata.title,
                short_title=metadata.short_title,
                authors_str=authors_formatted,
                year=metadata.year,
                discipline=metadata.discipline,
                research_type=metadata.research_type,
                page_numbers=mc["pages"],
                page_display=page_display,
                headings=mc["headings"]
            )

            final_chunks.append(TextChunk(
                chunk_id=chunk_id,
                text=mc["text"],
                metadata=chunk_meta
            ))

        return final_chunks

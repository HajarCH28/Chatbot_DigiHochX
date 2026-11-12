import json
import logging
from pathlib import Path
from typing import Optional

from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling_core.types.doc import DoclingDocument

logger = logging.getLogger(__name__)

class DoclingParser:
    """Manager für die Konvertierung akademischer PDFs mit Docling und lokalem Cache."""

    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path(".cache") / "docling"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # OCR für native digitale PDFs deaktivieren (Geschwindigkeitsvorteil und sauberer Text)
        pipeline_options = PdfPipelineOptions()
        pipeline_options.do_ocr = False
        
        self.converter = DocumentConverter(
            format_options={"pdf": PdfFormatOption(pipeline_options=pipeline_options)}
        )

    def _get_cache_path(self, pdf_path: Path) -> Path:
        safe_stem = pdf_path.stem[:40].replace(" ", "_")
        return self.cache_dir / f"{safe_stem}_{pdf_path.stat().st_size}.json"

    def parse_pdf(self, pdf_path: Path, use_cache: bool = True) -> DoclingDocument:
        """Konvertiert ein PDF in ein DoclingDocument, nutzt den Cache wenn verfügbar."""
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF-Datei nicht gefunden: {pdf_path}")

        cache_path = self._get_cache_path(pdf_path)
        if use_cache and cache_path.exists():
            logger.info("Lade aus Docling-Cache: %s", cache_path.name)
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return DoclingDocument.model_validate(data)

        logger.info("Docling-Konvertierung läuft für: %s", pdf_path.name)
        conv_res = self.converter.convert(pdf_path)
        doc = conv_res.document

        if use_cache:
            try:
                with open(cache_path, "w", encoding="utf-8") as f:
                    json.dump(doc.model_dump(mode="json"), f, ensure_ascii=False)
                logger.info("Dokument gecacht: %s", cache_path.name)
            except Exception as e:
                logger.warning("Cache-Speicherung fehlgeschlagen für %s: %s", pdf_path.name, e)

        return doc

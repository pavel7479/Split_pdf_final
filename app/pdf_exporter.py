from typing import List
import fitz
from pdf_processor import PdfProcessor
import os
import logging

logger = logging.getLogger(__name__)

class PdfExporter(PdfProcessor):
    """Класс для экспорта блоков в отдельные PDF."""
    def __init__(self, pdf_path: str, output_dir: str = './output'):
        super().__init__(pdf_path)
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def export_block_to_pdf(self, code: str, page_nums: List[int]) -> str:
        if not page_nums:
            return ""
        new_doc = fitz.open()
        for page_num in sorted(page_nums):
            new_doc.insert_pdf(self.doc, from_page=page_num, to_page=page_num)
        output_path = os.path.join(self.output_dir, f"{code}.pdf")
        new_doc.save(output_path)
        new_doc.close()
        logger.info(f"Создан PDF: {output_path}")
        return output_path
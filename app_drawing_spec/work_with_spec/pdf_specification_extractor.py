
import camelot
import pdfplumber
import pandas as pd
from typing import List, Optional


# --- 3. Извлечение ---
class PdfSpecificationExtractor:
    """Извлекает таблицы спецификации из PDF."""

    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path

    def extract(self, page_nums: Optional[List[int]] = None) -> List[pd.DataFrame]:
        tables = []

        if page_nums is None:
            with pdfplumber.open(self.pdf_path) as pdf:
                page_nums = list(range(1, len(pdf.pages)))

        for page_num in page_nums:
            # --- Camelot ---
            camelot_tables = camelot.read_pdf(self.pdf_path, pages=str(page_num + 1), flavor="lattice")
            if camelot_tables and len(camelot_tables) > 0:
                df = camelot_tables[0].df
            else:
                with pdfplumber.open(self.pdf_path) as pdf:
                    page = pdf.pages[page_num]
                    table = page.extract_table()
                    if not table:
                        continue
                    df = pd.DataFrame(table[1:], columns=table[0])

            tables.append(df)

        return tables
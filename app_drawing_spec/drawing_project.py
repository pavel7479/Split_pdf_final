import os
from pathlib import Path
from typing import List, Optional
import camelot
from pdf2image import convert_from_path
import pdfplumber
import pandas as pd
import re
import numpy as np
from specification_cleaner import SpecificationCleaner

class DrawingProject:
    """Представляет один проект чертежа (один PDF = 1 чертёж + спецификация)."""

    def __init__(self, pdf_path: str):
        self.pdf_path = Path(pdf_path)
        self.project_id = self.pdf_path.stem
        self.output_dir = self.pdf_path.parent / self.project_id

    def extract_drawing_page(self, page_num: int = 0) -> Optional[str]:
        """Сохраняет страницу с чертежом как PNG. По умолчанию берём первую страницу."""
        images = convert_from_path(self.pdf_path, first_page=page_num + 1, last_page=page_num + 1)
        if not images:
            return None
        output_path = self.output_dir / "drawing.png"
        os.makedirs(self.output_dir, exist_ok=True)
        images[0].save(output_path, "PNG")
        return str(output_path)
    
    def extract_specification(self, page_nums: Optional[List[int]] = None) -> Optional[str]:
        """Парсит таблицы спецификации со страниц PDF и сохраняет как Excel.
        Если page_nums=None — берём все страницы после первой.
        """
        os.makedirs(self.output_dir, exist_ok=True)
        output_path_raw = self.output_dir / "specification_raw.xlsx"
        output_path_clean = self.output_dir / "specification.xlsx"
        all_dfs_raw = []
        all_dfs_clean = []

        cleaner = SpecificationCleaner()

        try:
            # Если страницы не указаны — берём все после первой
            if page_nums is None:
                with pdfplumber.open(self.pdf_path) as pdf:
                    page_nums = list(range(1, len(pdf.pages)))

            for page_num in page_nums:
                # --- Camelot ---
                tables = camelot.read_pdf(str(self.pdf_path), pages=str(page_num + 1), flavor="lattice")
                if tables and len(tables) > 0:
                    df = tables[0].df
                else:
                    # --- pdfplumber fallback ---
                    with pdfplumber.open(self.pdf_path) as pdf:
                        page = pdf.pages[page_num]
                        table = page.extract_table()
                        if not table:
                            continue
                        df = pd.DataFrame(table[1:], columns=table[0])

                # сохраняем «как есть»
                all_dfs_raw.append(df)

                df_clean = cleaner.clean(df)
                if not df_clean.empty:
                    all_dfs_clean.append(df_clean)

            if not all_dfs_raw:
                return None

            final_raw = pd.concat(all_dfs_raw, ignore_index=True)
            final_raw.to_excel(output_path_raw, index=False)

            if not all_dfs_clean:
                return None

            # сохраняем очищенные таблицы
            final_clean = pd.concat(all_dfs_clean, ignore_index=True)
            final_clean.to_excel(output_path_clean, index=False)

            return str(output_path_clean)

        except Exception as e:
            print(f"[ERROR] Failed to extract specification: {e}")
            return None










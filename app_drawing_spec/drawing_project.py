import os
from pathlib import Path
from typing import List, Optional
import camelot
from pdf2image import convert_from_path
import pdfplumber
import pandas as pd
import re
import numpy as np
from app_drawing_spec.work_with_spec.specification_cleaner import SpecificationCleaner

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











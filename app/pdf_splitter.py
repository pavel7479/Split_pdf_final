from pdf_processor import PdfProcessor
from typing import Dict, List
import re

class PdfSplitter(PdfProcessor):
    """Класс для разбиения PDF на блоки по кодам, игнорируя оглавление."""
    def __init__(self, pdf_path: str):
        super().__init__(pdf_path)
        self.groups: Dict[str, List[int]] = {}

    def group_pages_by_code(self) -> list[tuple[str, list[int]]]:
        blocks = []
        current_code = None
        current_pages = []

        for page_num in range(len(self.doc)):
            text = self.extract_text_from_page(page_num)
            if len(text.strip()) < 50 and not self.has_drawings(page_num):
                # Пустая страница → пропускаем
                continue

            # Проверка кода на странице
            code = self.extract_code_from_page(page_num)

            # Если новая спецификация с другим кодом → закрываем текущий блок
            if code and current_code and code != current_code:
                if current_pages:
                    blocks.append((current_code, current_pages))
                current_code = code
                current_pages = [page_num]
                continue

            # Если нашли код и блок пустой → начинаем новый блок
            if code and not current_code:
                current_code = code
                current_pages = [page_num]
                continue

            # Если блок уже есть, добавляем страницу (drawing или spec)
            if current_code:
                current_pages.append(page_num)

        # Добавляем последний блок
        if current_code and current_pages:
            blocks.append((current_code, current_pages))

        return blocks

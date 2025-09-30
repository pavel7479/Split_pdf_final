import fitz  # PyMuPDF для работы с PDF
import re    # Для поиска кодов
from PIL import Image
import io
from typing import Optional

class PdfProcessor:
    """Базовый класс для общих операций с PDF."""
    def __init__(self, pdf_path: str):
        self.pdf_path = pdf_path
        self.doc = fitz.open(pdf_path)

    def close(self):
        if self.doc:
            self.doc.close()

    def extract_text_from_page(self, page_num: int) -> str:
        if 0 <= page_num < len(self.doc):
            return self.doc[page_num].get_text("text")
        return ""

    def extract_code_from_page(self, page_num: int) -> Optional[str]:
        text = self.extract_text_from_page(page_num)
        match = re.search(r'D\d+[A-Z0-9_]*Y', text)
        return match.group(0) if match else None

    def has_drawings(self, page_num: int) -> bool:
        return bool(self.doc[page_num].get_drawings())

    def render_page_to_image(self, page_num: int) -> Image.Image:
        page = self.doc[page_num]
        pix = page.get_pixmap(matrix=fitz.Matrix(2, 2))
        img_bytes = pix.tobytes("png")
        return Image.open(io.BytesIO(img_bytes)).convert('RGB')
    
    # Добавлен для извлечения заголовков чертежей
    def extract_title_from_page(self, page_num: int) -> Optional[str]:
        """
        Извлекает заголовок страницы (например 'OPERATOR’S CAB-4'),
        то есть текст перед кодом вида D...Y.
        Если заголовок не найден — возвращает None.
        """
        text = self.extract_text_from_page(page_num)

        # Ищем паттерн: <заголовок> <код>
        match = re.search(r'([\w\s\-\’]+?)\s+D\d+[A-Z0-9_]*Y', text)
        if match:
            title = match.group(1).strip()
            # убираем лишние пробелы и переносы строк и всё, что не латиница и ASCII
            title = re.sub(r'[^\x00-\x7F]+', '', title)
            return title

        return None


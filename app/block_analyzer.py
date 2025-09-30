from pdf_processor import PdfProcessor
import pdfplumber
import torch
from PIL import Image
from transformers import AutoModel, AutoTokenizer
import logging
import io
from typing import List, Optional, Tuple
import re
import camelot

logger = logging.getLogger(__name__)

class BlockAnalyzer:
    """Класс для анализа блоков с MiniCPM для сомнительных случаев."""
    def __init__(self, processor: PdfProcessor):
        self.processor = processor
        self.model = AutoModel.from_pretrained(
            'openbmb/MiniCPM-V-4_5',
            trust_remote_code=True,
            attn_implementation='sdpa',
            torch_dtype=torch.bfloat16
        ).eval()

        # ✅ Проверяем доступность GPU
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            logger.info(f"Используется GPU: {device_name}")
            self.model = self.model.cuda()
        else:
            logger.warning("GPU недоступен, модель будет работать на CPU")

        self.tokenizer = AutoTokenizer.from_pretrained(
            'openbmb/MiniCPM-V-4_5',
            trust_remote_code=True
        )

    def is_specification(self, page_num: int) -> bool:
        tables = camelot.read_pdf(self.processor.pdf_path, pages=str(page_num + 1))  # Camelot → 1-индексация
        return len(tables) > 0
    
    def classify_with_minicpm(self, page_num: int) -> Tuple[str, Optional[str], Optional[str]]:
        logger.info(f"[MiniCPM] Классификация страницы {page_num} начата")
        
        code = self.processor.extract_code_from_page(page_num)
        title = self.processor.extract_title_from_page(page_num)
        logger.info(f"[MiniCPM] Извлечён код={code}, заголовок={title}")

        # --- случай 1: регулярка нашла код ---
        if code:
            page_type = "specification" if self.is_specification(page_num) else "drawing"
            logger.info(f"[MiniCPM] Регулярка нашла код, предварительный тип: {page_type}")

            try:
                image = self.processor.render_page_to_image(page_num)
                logger.info(f"[MiniCPM] Рендер страницы {page_num} в изображение завершён")
                short_prompt = """
                Classify this PDF page strictly as one of:
                - drawing
                - specification
                - drawing_specification
                - ignore
                Return only the type, nothing else.
                """

                msgs = [{'role': 'user', 'content': [image, short_prompt]}]
                response = self.model.chat(image=image, msgs=msgs, tokenizer=self.tokenizer)
                page_type = response.strip().split()[0]
                logger.info(f"[MiniCPM] MiniCPM вернул page_type={page_type}")

            except Exception as e:
                logger.warning(f"[MiniCPM] Ошибка классификации страницы {page_num}: {e}")

            return page_type, code, title

        # --- случай 2: регулярка не нашла код ---
        try:
            image = self.processor.render_page_to_image(page_num)
            logger.info(f"[MiniCPM] Рендер страницы {page_num} для полного анализа")
            long_prompt = """
            You are a PDF page classifier. Each page may be:
            - drawing
            - specification
            - ignore

            Classify strictly as one of these types:
            - drawing: Technical drawings, exploded views, diagrams with arrows, callouts, or part breakdowns.
            - specification: Tables listing spare parts with columns POS, ITEM, CODE, DESCRIPTION, QTY, REMARK. Must contain numeric POS/QTY entries.
            - ignore: All other pages (titles, preface, table of contents, logos, decorative images, etc.).

            Rules:
            - A specification page can only appear immediately after a drawing page.
            - If the previous page was ignore, this page cannot be specification.
            - Do NOT classify as specification if it is only a table of contents or section list.
            - Do NOT classify as drawing if the page only has logos, icons, or simple illustrations.

            Return only one word: drawing, specification, or ignore.

            """

            # long_prompt = """
            # You are a PDF page classifier. Each page may contain:
            # - drawing
            # - specification
            # - drawing_specification
            # - ignore

            # If no drawing code is visible, try to extract the TITLE (only in Latin letters, digits, spaces, - and ()). 
            # Ignore Chinese or other non-Latin characters.

            # Return strictly: type,code,title
            # Example: drawing,null,DRIVING BRAKE SYSTEM(TWO)
            # Example: specification,null,LODER BOOM MODULE
            # Example: ignore,null,null
            # """
            msgs = [{'role': 'user', 'content': [image, long_prompt]}]
            response = self.model.chat(image=image, msgs=msgs, tokenizer=self.tokenizer)
            logger.info(f"[MiniCPM] MiniCPM вернул: {response}")

            parts = [p.strip() for p in response.split(',')]
            page_type = parts[0] if len(parts) > 0 else "unknown"
            code = parts[1] if len(parts) > 1 and parts[1] != "null" else None
            title = parts[2] if len(parts) > 2 and parts[2] != "null" else None

            # фильтруем заголовок
            if title:
                title = re.sub(r'[^A-Za-z0-9\-\s\(\)]', '', title).strip()
                if not title:
                    title = None

            logger.info(f"[MiniCPM] Финальный результат: page_type={page_type}, code={code}, title={title}")
            return page_type, code, title

        except Exception as e:
            logger.error(f"[MiniCPM] Ошибка MiniCPM на странице {page_num}: {e}")
            return "unknown", None, None

    def analyze_block(self, page_nums: list[int]) -> tuple[Optional[str], list[int]]:
        """
        Строим блок: один чертёж + все спецификации с тем же кодом и названием.
        Возвращает (код, [drawing_page, spec_pages...]).
        """
        if not page_nums:
            return None, []

        drawing_page = None
        code = None
        title = None
        valid_pages = []

        for p in page_nums:
            page_type, extracted_code, extracted_title = self.classify_with_minicpm(p)

            if page_type == "ignore":
                continue

            # Старт блока → чертёж или чертёж+спецификация
            if page_type in ("drawing", "drawing_specification"):
                drawing_page = p
                code = extracted_code
                title = extracted_title
                valid_pages.append(p)

                if page_type == "drawing_specification":
                    valid_pages.append(p)
                break

        if not drawing_page or not code:
            return None, []

        # добавляем спецификации с тем же кодом + тем же заголовком
        for p in page_nums:
            if p <= drawing_page:
                continue
            page_type, extracted_code, extracted_title = self.classify_with_minicpm(p)

            if page_type == "specification" and extracted_code == code:
                valid_pages.append(p)
            elif page_type in ("drawing", "drawing_specification"):
                # новый блок, если код или название отличается
                if extracted_code != code or (title and extracted_title and extracted_title != title):
                    break
                else:
                    # если код тот же и название совпадает → дубликат чертежа, пропускаем
                    continue

        return code, valid_pages

    def is_continuation_of_spec(self, page_num: int, current_key: Optional[str] = None) -> bool:
        """
        Проверяет, является ли страница продолжением спецификации.
        Логика:
        1. Если title+code совпадает с current_key → продолжаем.
        2. Если в тексте есть признаки таблицы (POS ITEM) или несколько подряд идущих номеров → тоже продолжаем.
        """
        text = self.processor.extract_text_from_page(page_num)

        # --- исправление 1: проверяем совпадение ключа ---
        if current_key:
            code = self.processor.extract_code_from_page(page_num)
            title = self.processor.extract_title_from_page(page_num)
            block_key = f"{title} {code}" if code and title else code
            if block_key == current_key:
                return True

        # --- старая логика (оставляем) ---
        if re.search(r"\bPOS\b", text) and re.search(r"\bITEM\b", text):
            return True

        pos_numbers = re.findall(r"^\s*\d+\s", text, re.MULTILINE)
        if len(pos_numbers) >= 3:
            return True

        return False
  
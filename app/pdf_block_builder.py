import logging
from pdf_processor import PdfProcessor
from pdf_splitter import PdfSplitter
from block_analyzer import BlockAnalyzer
from pdf_exporter import PdfExporter
from typing import List, Optional
import os
import re

logger = logging.getLogger(__name__)

class PdfBlockBuilder:
    def __init__(self, exporter, analyzer):
        self.exporter = exporter
        self.analyzer = analyzer

        self.current_key: Optional[str] = None
        self.current_pages: list[int] = []
        self.output_files: list[str] = []

        # уже встреченные коды (чтобы при повторе кода добавлять title+code)
        self.seen_codes: set[str] = set()

        # временные спецификации до чертежа: key->list[page_nums]
        self.pending_specs: dict[str, list[int]] = {}

    def _make_block_key(self, code: Optional[str], title: Optional[str] = None) -> Optional[str]:
        """Формируем уникальный ключ для блока.
        - Если code не подходит под регулярку → None (отбраковка).
        - Если code уже встречался с другим title → формируем "title code".
        - Если code первый раз → используем просто code.
        - Если только title без кода → используем title.
        """
        if not code and not title:
            return None

        # проверка валидности кода (пример: только буквы+цифры, до 20 символов)
        import re
        if code and not re.fullmatch(r"[A-Z0-9]{5,20}", code):
            return None

        # оба есть: code и title
        if code and title:
            # если этот код уже был, но с другим title → различаем по title
            if code in self.seen_codes:
                return f"{title.strip()} {code}".strip()
            return code

        # только code
        if code:
            return code

        # только title
        if title:
            return title.strip()

        return None

    def start_new_block(self, page_num: int, code: Optional[str] = None, title: Optional[str] = None):
        """Начинаем новый блок (чертёж или чертёж+спецификация)."""
        new_key = self._make_block_key(code, title)
        if new_key is None:
            logger.info(f"[Builder] Страница {page_num} пропущена: нет кода и названия")
            return

        # Если блок тот же самый — просто добавляем страницу
        if self.current_key == new_key:
            if page_num not in self.current_pages:
                self.current_pages.append(page_num)
            return

        # Сохраняем предыдущий блок
        if self.current_pages and self.current_key:
            out = self.exporter.export_block_to_pdf(self.current_key, self.current_pages)
            if out:
                self.output_files.append(out)

        # Начинаем новый блок
        self.current_key = new_key
        self.current_pages = [page_num]

        # Обновляем список встреченных кодов
        if code:
            # Если код уже был, но с другим названием — ключ уже уникализирован в _make_block_key
            self.seen_codes.add(code)

        # Приклеиваем отложенные спецификации
        if new_key in self.pending_specs:
            pages = self.pending_specs.pop(new_key)
            for p in pages:
                if p not in self.current_pages:
                    self.current_pages.append(p)

        logger.info(f"[Builder] Новый блок: {self.current_key}, страницы={self.current_pages}")

    def add_specification(self, page_num: int, code: Optional[str] = None, title: Optional[str] = None):
        key = self._make_block_key(code, title)
        if key is None:
            logger.info(f"[Builder] Страница {page_num} пропущена: нет кода и названия")
            return

        if not self.current_key:
            self.pending_specs.setdefault(key, []).append(page_num)
            return

        if key == self.current_key or self.analyzer.is_continuation_of_spec(page_num, self.current_key):
            if page_num not in self.current_pages:
                self.current_pages.append(page_num)
            return

        self.pending_specs.setdefault(key, []).append(page_num)

    def finalize(self):
        if self.current_pages and self.current_key:
            out = self.exporter.export_block_to_pdf(self.current_key, self.current_pages)
            if out:
                self.output_files.append(out)

        if self.pending_specs:
            logger.info(f"[Builder] Отброшены несопоставленные спецификации: {list(self.pending_specs.keys())}")
            self.pending_specs.clear()

        return self.output_files






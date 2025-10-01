
import logging
import re
from dataclasses import dataclass
from typing import Optional, Tuple, List

# ---------- Настройка логирования ----------
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)  # можно заменить на INFO в проде

console = logging.StreamHandler()
console.setLevel(logging.DEBUG)
formatter = logging.Formatter("[%(levelname)s] %(message)s")
console.setFormatter(formatter)

if not logger.hasHandlers():
    logger.addHandler(console)


# ---------- Результат анализа ----------
@dataclass
class PageAnalysisResult:
    page_number: int
    has_specification: bool
    title: Optional[str] = None
    table_area: Optional[Tuple[float, float, float, float]] = None  # (x0, top, x1, bottom)


# ---------- Анализатор страниц ----------
class PageAnalyzer:
    """Анализирует PDF-страницу и определяет, есть ли на ней спецификация."""

    def __init__(self, min_header_hits: int = 2):
        self.min_header_hits = min_header_hits
        self.header_keywords = ["POS", "CODE", "DESCRIPTION", "QTY", "REMARK", "ITEM"]

    def analyze(self, page, page_number: int) -> PageAnalysisResult:
        """Главный метод-оркестратор анализа страницы."""
        logger.info(f"[Page {page_number}] Начинаем анализ страницы")

        lines = self._extract_lines(page, page_number)
        title = self._detect_title(lines, page_number)
        header_hits = self._detect_headers(lines, page_number)

        has_spec = header_hits >= self.min_header_hits
        logger.info(f"[Page {page_number}] Признаки спецификации: {has_spec}")

        table_area = self._detect_table_area(page, page_number) if has_spec else None

        return PageAnalysisResult(
            page_number=page_number,
            has_specification=has_spec,
            title=title,
            table_area=table_area,
        )

    # ---------- Вспомогательные методы ----------

    def _extract_lines(self, page, page_number: int) -> List[str]:
        """Извлекает текстовые строки со страницы."""
        text = page.extract_text(x_tolerance=2, y_tolerance=2) or ""
        lines = [l.strip() for l in text.splitlines() if l.strip()]
        logger.debug(f"[Page {page_number}] Извлечено строк: {len(lines)}")
        return lines

    def _detect_title(self, lines: List[str], page_number: int) -> Optional[str]:
        """Определяет заголовок спецификации (если есть)."""
        if not lines:
            return None

        first_line = lines[0]
        if re.search(r"[A-Z]{2,}", first_line) and len(first_line.split()) > 1:
            logger.info(f"[Page {page_number}] Найден заголовок: {first_line}")
            return first_line

        logger.debug(f"[Page {page_number}] Заголовок не найден")
        return None

    def _detect_headers(self, lines: List[str], page_number: int) -> int:
        """Подсчитывает количество совпадений с ключевыми словами в заголовках."""
        header_hits = 0
        for line in lines[:5]:  # смотрим только первые строки
            for kw in self.header_keywords:
                if re.search(rf"\b{kw}\b", line, re.IGNORECASE):
                    header_hits += 1
        logger.debug(f"[Page {page_number}] Найдено ключевых слов: {header_hits}")
        return header_hits

    def _detect_table_area(self, page, page_number: int) -> Optional[Tuple[float, float, float, float]]:
        """Определяет область таблицы на странице (bbox)."""
        try:
            table = page.extract_table()
            if not table:
                logger.debug(f"[Page {page_number}] Таблица не найдена")
                return None

            bbox = page.bbox  # (x0, top, x1, bottom)
            logger.info(f"[Page {page_number}] Найдена таблица в области {bbox}")
            return bbox
        except Exception as e:
            logger.error(f"[Page {page_number}] Ошибка при извлечении таблицы: {e}")
            return None








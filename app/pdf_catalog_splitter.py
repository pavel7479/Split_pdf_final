import logging
from pdf_block_builder import PdfBlockBuilder
from pdf_processor import PdfProcessor
from pdf_splitter import PdfSplitter
from block_analyzer import BlockAnalyzer
from pdf_exporter import PdfExporter
from typing import List, Optional
import os
import re

logger = logging.getLogger(__name__)


class PdfCatalogSplitter:
    """Главный класс-оркестратор для разбиения PDF на пары чертёж + все спецификации."""
    def __init__(self, pdf_path: str, output_dir: str = './output'):
        self.processor = PdfProcessor(pdf_path)
        self.splitter = PdfSplitter(pdf_path)
        self.analyzer = BlockAnalyzer(self.processor)
        self.exporter = PdfExporter(pdf_path, output_dir)
        logger = logging.getLogger(__name__)
        logger.info(f"Инициализация PdfCatalogSplitter для файла: {pdf_path}")
    
    def process(self) -> list[str]:
        total_pages = len(self.processor.doc)
        logger.info(f"Начало обработки PDF: {total_pages} страниц всего")

        builder = PdfBlockBuilder(self.exporter, self.analyzer)

        for page_num in range(total_pages):
            logger.info(f"Обработка страницы {page_num}")
            logger.info(f"Вызов analyzer.classify_with_minicpm для страницы {page_num}")

            page_type, code, title = self.analyzer.classify_with_minicpm(page_num)
            logger.info(f"Page {page_num}: result from analyzer -> type={page_type}, code={code}, title={title}")

            # если страница мусор
            if page_type in ("ignore", "unknown"):
                logger.info(f"Page {page_num}: ignored")
                continue

            # если это чертёж (возможно со спецификацией)
            if page_type in ("drawing", "drawing_specification"):
                logger.info("Действие: start_new_block")
                builder.start_new_block(page_num, code=code, title=title)
                logger.info(f"Блок после start_new_block: current_key={builder.current_key}, страницы={builder.current_pages}")

                if page_type == "drawing_specification":
                    logger.info("Действие: add_specification (drawing_specification)")
                    builder.add_specification(page_num, code=code, title=title)
                    logger.info(f"Блок после add_specification: current_key={builder.current_key}, страницы={builder.current_pages}")
                continue

            # если это спецификация
            if page_type == "specification":
                logger.info("Действие: add_specification (specification)")
                builder.add_specification(page_num, code=code, title=title)
                logger.info(f"Блок после add_specification: current_key={builder.current_key}, страницы={builder.current_pages}")
                continue

        # финализируем
        output_files = builder.finalize()
        logger.info(f"Финализация блоков, всего сгенерировано {len(output_files)} файлов")
        logger.info(f"Сгенерированные файлы: {output_files}")
        return output_files

    def __del__(self):
        import logging
        logger = logging.getLogger(__name__)
        if hasattr(self, 'processor') and self.processor and hasattr(self.processor, 'doc') and self.processor.doc:
            self.processor.close()
        if hasattr(self, 'splitter') and self.splitter and hasattr(self.splitter, 'doc') and self.splitter.doc:
            self.splitter.close()
        if hasattr(self, 'exporter') and self.exporter and hasattr(self.exporter, 'doc') and self.exporter.doc:
            self.exporter.close()
        logger.info("Ресурсы PdfCatalogSplitter закрыты")
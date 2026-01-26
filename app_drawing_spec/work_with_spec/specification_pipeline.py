import os
import pandas as pd
from typing import Optional

from app_drawing_spec.work_with_spec.pdf_specification_extractor import PdfSpecificationExtractor
from app_drawing_spec.work_with_spec.specification_cleaner import SpecificationCleaner
from app_drawing_spec.work_with_spec.specification_normalizer import SpecificationNormalizer


# --- 4. Конвейер ---
class SpecificationPipeline:
    """Общий конвейер: парсинг → чистка → нормализация → сохранение."""

    def __init__(self, pdf_path: str, output_dir: str, llm_client):
        self.extractor = PdfSpecificationExtractor(pdf_path)
        self.cleaner = SpecificationCleaner()
        self.normalizer = SpecificationNormalizer(llm_client)
        self.output_dir = output_dir

    def run(self) -> Optional[str]:
        os.makedirs(self.output_dir, exist_ok=True)
        output_path = os.path.join(self.output_dir, "specification.xlsx")

        try:
            raw_tables = self.extractor.extract()
            cleaned_tables = [self.cleaner.clean(df) for df in raw_tables if not df.empty]

            if not cleaned_tables:
                return None

            merged_df = pd.concat(cleaned_tables, ignore_index=True)

            # финальная нормализация LLM
            final_df = self.normalizer.normalize(merged_df)

            final_df.to_excel(output_path, index=False)
            return output_path

        except Exception as e:
            print(f"[ERROR] Pipeline failed: {e}")
            return None
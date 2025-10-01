import sys
sys.path.append('/root/Split_Pdf')

from app_drawing_spec.drawing_exporter import DrawingExporter
from app_drawing_spec.drawing_project import DrawingProject
from pathlib import Path
from app_drawing_spec.work_with_spec.specification_pipeline import SpecificationPipeline


class DrawingPipeline:
    """Оркестратор, который находит PDF и запускает обработку (чертёж + спецификация)."""

    def __init__(self, input_dir: str):
        self.input_dir = Path(input_dir)

    def run(self):
        pdf_files = list(self.input_dir.glob("*.pdf"))
        if not pdf_files:
            print("[WARN] No PDF files found.")
            return

        for pdf_file in pdf_files:
            print(f"[INFO] Processing {pdf_file.name}...")

            # --- 1. Создаём проект и экспортируем чертёж ---
            project = DrawingProject(pdf_file)
            exporter = DrawingExporter(project)
            drawing_path = exporter.export()
            print(f"[INFO] Drawing saved to: {drawing_path}")

            # --- 2. Запускаем пайплайн спецификации ---
            spec_pipeline = SpecificationPipeline(pdf_path=pdf_file, output_dir=project.output_dir)
            spec_path = spec_pipeline.run()
            if spec_path:
                print(f"[INFO] Specification saved to: {spec_path}")
            else:
                print(f"[WARN] No specification extracted for {pdf_file.name}")


if __name__ == "__main__":
    # Пример запуска
    pipeline = DrawingPipeline(
        input_dir="/root/Split_Pdf/for_test/отладка"
    )
    pipeline.run()

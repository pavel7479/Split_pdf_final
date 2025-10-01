import sys
sys.path.append('/root/Split_Pdf')

from app_drawing_spec.drawing_exporter import DrawingExporter
from app_drawing_spec.drawing_project import DrawingProject
from pathlib import Path

class DrawingPipeline:
    """Оркестратор, который находит PDF и запускает обработку."""

    def __init__(self, input_dir: str):
        self.input_dir = Path(input_dir)

    def run(self):
        pdf_files = list(self.input_dir.glob("*.pdf"))
        if not pdf_files:
            print("[WARN] No PDF files found.")
            return

        for pdf_file in pdf_files:
            print(f"[INFO] Processing {pdf_file.name}...")
            project = DrawingProject(pdf_file)
            exporter = DrawingExporter(project)
            exporter.export()

if __name__ == "__main__":
    # Пример запуска
    pipeline = DrawingPipeline(input_dir="/root/Split_Pdf/for_test/отладка/26_QUY260CR 32Y Crawler Crane Spare parts catalog-248-278")
    pipeline.run()
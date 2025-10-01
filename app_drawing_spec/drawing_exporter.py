
from app_drawing_spec.drawing_project import DrawingProject

class DrawingExporter:
    """Отвечает за сохранение чертежа (PNG)."""

    def __init__(self, project: DrawingProject):
        self.project = project

    def export(self) -> str:
        """
        Экспортирует чертёж в PNG.
        Возвращает путь к файлу или None.
        """
        drawing_path = self.project.extract_drawing_page()

        if drawing_path:
            print(f"[INFO] Drawing exported for {self.project.project_id}: {drawing_path}")
        else:
            print(f"[WARN] Drawing export failed for {self.project.project_id}")

        return drawing_path

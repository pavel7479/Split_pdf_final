
from app_drawing_spec.drawing_project import DrawingProject


class DrawingExporter:
    """Отвечает за сохранение файлов проекта."""

    def __init__(self, project: DrawingProject):
        self.project = project

    def export(self) -> None:
        """Выполняет экспорт в папку: PNG + Excel."""
        drawing_path = self.project.extract_drawing_page()
        spec_path = self.project.extract_specification()

        print(f"[INFO] Export complete for {self.project.project_id}:")
        print(f"       drawing → {drawing_path}")
        print(f"       specification → {spec_path}")
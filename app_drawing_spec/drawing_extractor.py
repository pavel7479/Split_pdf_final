import logging
from pathlib import Path
from typing import Optional

from pdf2image import convert_from_path
from PIL import Image

logger = logging.getLogger(__name__)


class DrawingExtractor:
    def __init__(self, pdf_path: str | Path, dpi: int = 300, poppler_path: Optional[str] = None):
        self.pdf_path = Path(pdf_path)
        self.dpi = dpi
        self.poppler_path = poppler_path

    def extract_drawing_page(
        self,
        page_num: int = 0,
        output_dir: Optional[str | Path] = None,
        output_name: str = "drawing.png",
        force_overwrite: bool = True,
    ) -> Optional[str]:
        # Оркестрация: валидация -> подготовка папки -> рендер -> сохранение
        if not self._validate_pdf():
            return None

        out_dir = self._compute_output_dir(output_dir)
        image = self._render_page(page_num)
        if image is None:
            return None

        return self._save_image(image, out_dir, output_name, force_overwrite)

    # --- приватные вспомогательные методы ---

    def _validate_pdf(self) -> bool:
        if not self.pdf_path.exists():
            logger.error("PDF not found: %s", str(self.pdf_path))
            return False
        return True

    def _compute_output_dir(self, output_dir: Optional[str | Path]) -> Path:
        if output_dir:
            out_dir = Path(output_dir)
        else:
            out_dir = self.pdf_path.parent / self.pdf_path.stem
        try:
            out_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.exception("Failed to create output directory %s: %s", out_dir, e)
            raise
        return out_dir

    def _render_page(self, page_num: int) -> Optional[Image.Image]:
        try:
            images = convert_from_path(
                str(self.pdf_path),
                dpi=self.dpi,
                first_page=page_num + 1,
                last_page=page_num + 1,
                poppler_path=self.poppler_path,
            )
            if not images:
                logger.warning("No images returned when converting page %d of %s", page_num, self.pdf_path)
                return None
            return images[0]
        except Exception as e:
            logger.exception("Error converting page %d of %s: %s", page_num, self.pdf_path, e)
            return None

    def _save_image(self, image: Image.Image, out_dir: Path, output_name: str, force_overwrite: bool) -> Optional[str]:
        output_path = out_dir / output_name
        try:
            if output_path.exists() and not force_overwrite:
                logger.info("Output already exists and overwrite disabled: %s", output_path)
                return str(output_path)

            image.save(output_path, format="PNG")
            logger.info("Saved drawing page -> %s (dpi=%d)", output_path, self.dpi)
            return str(output_path)
        except Exception as e:
            logger.exception("Failed to save image %s: %s", output_path, e)
            return None

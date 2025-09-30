import logging
from pdf_catalog_splitter import PdfCatalogSplitter

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler('pdf_processing.log'), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

def main():
    input_path = '/root/Split_Pdf/for_test/39_RT100 Rough Terrain Crane Spare parts catalog-1-50.pdf'
    output_dir = '/root/Split_Pdf/for_test/rezult3'

    logger.info(f"Запуск обработки файла: {input_path}")
    splitter = PdfCatalogSplitter(input_path, output_dir=output_dir)
    results = splitter.process()
    logger.info("Сгенерированные файлы: %s", results)
    print("Сгенерированные файлы:", results)

if __name__ == "__main__":
    main()
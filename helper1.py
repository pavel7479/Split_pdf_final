import sys
sys.path.append('/root/Split_pdf/app')

import sys
sys.path.append('/root/Split_pdf/app')

from pdf_catalog_splitter import PdfBlockBuilder

print("PdfBlockBuilder импортирован успешно")

# Заглушка для экспортера (не создаёт PDF, только логирует)
class DummyExporter:
    def export_block_to_pdf(self, code, page_nums):
        print(f"Экспорт: {code} -> страницы {page_nums}")
        return f"{code}.pdf"

exporter = DummyExporter()
builder = PdfBlockBuilder(exporter, None)

# Тестовые страницы
# Стр. 0: спецификация до чертежа
builder.add_specification(0, code="D00755700000020000Y", title="TEST TITLE")
# Стр. 1: чертёж
builder.start_new_block(1, code="D00755700000020000Y", title="TEST TITLE")
# Стр. 2: спецификация после чертежа
builder.add_specification(2, code="D00755700000020000Y", title="TEST TITLE")

# Финализируем
builder.finalize()


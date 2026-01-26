import pandas as pd
import numpy as np
import re
import re
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

class SpecificationCleaner:
    """Очищает DataFrame спецификации от заголовков, пустых строк, секций."""

    # можно вынести эти паттерны в конструктор / конфиг при желании
    HEADER_TOKENS = {"POS", "POS.", "POS:", "ITEM", "QTY", "QTY.", "CODE", "REMARK", "DESCRIPTION"}
    SECTION_WORD = re.compile(r"\bSYSTEM\b", flags=re.IGNORECASE)
    # Эвристика: строка — заголовок/раздел, если мало цифр, много заглавных слов и короткая по символам
    TITLE_WORDS_MAX = 6
    TITLE_CHAR_MAX = 60

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return df

        # 1) Normalize: strip strings, replace whitespace-only with NaN
        df = df.astype(object).where(pd.notnull(df), None)  # гарантируем object dtype
        df = df.applymap(lambda x: x.strip() if isinstance(x, str) else x)
        df = df.replace(r'^\s*$', np.nan, regex=True)

        # 2) Drop fully empty rows/cols
        df = df.dropna(how="all", axis=0).dropna(how="all", axis=1)

        if df.empty:
            return df

        # 3) Remove repeated header rows anywhere in table
        def is_header_row(row):
            # если хотя бы половина колонок содержат заголовочные токены — считаем это header row
            tokens = [str(c).upper().rstrip(":").strip() for c in row.fillna("").tolist()]
            matches = sum(1 for t in tokens if t in self.HEADER_TOKENS)
            return matches >= (len(tokens) / 2) and matches > 0

        header_mask = df.apply(is_header_row, axis=1)
        if header_mask.any():
            logger.debug(f"Removing {header_mask.sum()} detected header rows")
            df = df[~header_mask]

        # 4) Remove rows which entirely are section titles like "BOOM\nSYSTEM" or "BOOM SYSTEM"
        def is_section_title(row):
            # объединяем строку в единый текст по всем столбцам
            joined = " ".join([str(c) for c in row.fillna("").tolist()]).strip()
            if not joined:
                return False
            # если содержит ключевое слово SYSTEM → убрать
            if self.SECTION_WORD.search(joined):
                return True
            # эвристика: много слов, все заглавные и мало цифр — вероятно заголовок
            words = [w for w in re.split(r"\s+", joined) if w]
            if 0 < len(words) <= self.TITLE_WORDS_MAX and len(joined) <= self.TITLE_CHAR_MAX:
                alpha_words = sum(1 for w in words if re.match(r"^[A-Z0-9'\-()]+$", w))
                digits = sum(1 for w in words if re.search(r"\d", w))
                if alpha_words >= len(words) and digits == 0 and len(words) <= self.TITLE_WORDS_MAX:
                    return True
            return False

        sec_mask = df.apply(is_section_title, axis=1)
        if sec_mask.any():
            logger.debug(f"Removing {sec_mask.sum()} section/title rows")
            df = df[~sec_mask]

        # 5) Remove rows where first column equals header tokens (robustly)
        first_col = df.columns[0]
        df = df[~df[first_col].astype(str).str.upper().str.rstrip(":").str.strip().isin(self.HEADER_TOKENS)]

        # 6) Final cleanup: drop empty rows/cols, dedupe and reset index
        df = df.dropna(how="all", axis=0).dropna(how="all", axis=1)
        df = df.drop_duplicates().reset_index(drop=True)

        return df


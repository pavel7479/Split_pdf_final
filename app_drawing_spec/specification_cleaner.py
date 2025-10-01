import pandas as pd
import numpy as np
import re

class SpecificationCleaner:
    """Очищает DataFrame спецификации от заголовков, пустых строк, секций."""

    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return df

        # заменяем пустые строки на NaN
        df = df.replace(r'^\s*$', np.nan, regex=True)

        # убираем полностью пустые строки и столбцы
        df = df.dropna(how="all", axis=0)
        df = df.dropna(how="all", axis=1)

        # убираем дубли заголовков
        if "POS" in df.iloc[:, 0].values:
            df = df[df.iloc[:, 0] != "POS"]
        if "POS." in df.iloc[:, 0].values:
            df = df[df.iloc[:, 0] != "POS."]

        # убираем строки-заголовки типа "BOOM SYSTEM"
        mask = df.iloc[:, 0].astype(str).str.contains(r"SYSTEM", na=False, flags=re.IGNORECASE)
        df = df[~mask]

        # финальная зачистка
        df = df.dropna(how="all", axis=0)
        df = df.drop_duplicates().reset_index(drop=True)

        return df

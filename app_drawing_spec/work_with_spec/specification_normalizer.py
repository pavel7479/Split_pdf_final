import pandas as pd
from app_drawing_spec.LLM.llm_client import LLMClient

# --- 2. Нормализация через LLM ---
class SpecificationNormalizer:
    """Использует LLM для приведения спецификации к единому виду."""

    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client

    def normalize(self, df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return df

        # 1. Формируем подсказку для модели
        system_prompt = (
            "You are an assistant that cleans and normalizes technical specification tables "
            "extracted from engineering PDFs. "
            "Always preserve data. Do not invent missing rows or values. "
            "Your tasks:\n"
            "- Detect the specification TITLE. It may be located above the table or inside the first row(s).\n"
            "- Normalize the column headers. Possible target sets:\n"
            "  1. ['POS.', 'CODE', 'DESCRIPTION', 'QTY.', 'REMARK']\n"
            "  2. ['POS.', 'ITEM', 'DESCRIPTION & SPECIFICATION', 'QTY.']\n"
            "- If headers are missing or numeric (0,1,2,...), infer correct headers from context.\n"
            "- If the table is continued on another page without headers, keep the same normalized headers.\n"
            "- Return the result strictly as CSV (comma separated)."
        )

        user_prompt = f"""
        Here is a raw table extracted from PDF (first rows shown):

        {df.head(20).to_csv(index=False)}

        Please:
        - Identify and output the specification TITLE if present.
        - Replace ambiguous column names (e.g., '0', '1', '2') with correct headers.
        - Normalize the headers to one of the target sets above.
        - Return the full normalized table in CSV format.
        """

        # 2. Отправляем в LLM
        response = self.llm.query(
            system_prompt,
            user_prompt,
            temperature=0.1,
            top_p=0.9,
            repeat_penalty=1.2,
            num_beams=50,
            do_sample=False
        )

        # 3. Преобразуем обратно в DataFrame
        try:
            from io import StringIO
            df_norm = pd.read_csv(StringIO(response))
            return df_norm
        except Exception as e:
            print(f"[WARN] Failed to parse LLM response, fallback to original: {e}")
            return df

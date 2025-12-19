import json
import pandas as pd
from openai import OpenAI
from core.config import settings
from core.prompts import SEO_ANALYSIS_PROMPT
from services.sheets_service import SheetsService
from tools.seo_tools import normalize_seo_dataframe

class SEOAgent:
    def __init__(self):
        # LiteLLM client for Gemini
        self.client = OpenAI(
            api_key=settings.LITELLM_API_KEY,
            base_url=settings.LITELLM_BASE_URL
        )
        self.sheets_service = SheetsService()

    def answer_question(self, query: str, spreadsheet_id: str):
        """
        Executes SEO analysis: Ingest Sheets -> Normalize -> LLM Reasoning.
        """
        try:
            # 1. Live data ingestion from Google Sheets
            df = self.sheets_service.get_spreadsheet_data(spreadsheet_id)
            
            if df.empty:
                return "The SEO audit sheet appears to be empty or inaccessible."

            # 2. Normalize schema to handle column name changes safely
            df = normalize_seo_dataframe(df)

            # 3. Extract key metrics for LLM context
            # This handles Tier 2 grouping and aggregations
            context = self._extract_audit_summary(df)

            # 4. Generate final insight with Gemini
            return self._get_ai_reasoning(query, context)

        except Exception as e:
            return f"SEO Agent Error: {str(e)}"

    def _extract_audit_summary(self, df: pd.DataFrame):
        """
        Calculates ground-truth metrics to prevent AI hallucinations.
        """
        summary = {
            "total_urls": len(df),
            "indexability_status": df['indexability'].value_counts().to_dict() if 'indexability' in df.columns else {},
            "status_codes": df['status_code'].value_counts().to_dict() if 'status_code' in df.columns else {}
        }

        # Specific Tier 2 Logic: HTTPS and Title Lengths
        if 'address' in df.columns:
            non_https = df[~df['address'].str.startswith('https', na=False)]
            summary["non_https_count"] = len(non_https)
            summary["non_https_samples"] = non_https['address'].head(5).tolist()

        if 'title_length' in df.columns:
            long_titles = df[df['title_length'].astype(float) > 60]
            summary["long_titles_count"] = len(long_titles)
            summary["long_titles_samples"] = long_titles[['address', 'title_length']].head(5).to_dict(orient='records')

        return summary

    def _get_ai_reasoning(self, query: str, context: dict):
        """
        Calls Gemini to explain technical SEO health based on the extracted data.
        """
        response = self.client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": SEO_ANALYSIS_PROMPT},
                {"role": "user", "content": f"Audit Context: {json.dumps(context)}\n\nQuestion: {query}"}
            ]
        )
        return response.choices[0].message.content
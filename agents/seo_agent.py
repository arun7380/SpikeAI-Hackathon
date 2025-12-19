import json
import time
import pandas as pd
from openai import OpenAI, RateLimitError, APIError
from core.config import settings
from core.prompts import SEO_ANALYSIS_PROMPT
from services.sheets_service import SheetsService
from tools.seo_tools import normalize_seo_dataframe

class SEOAgent:
    def __init__(self):
        # LiteLLM client pointing to the hackathon proxy
        self.client = OpenAI(
            api_key=settings.LITELLM_API_KEY,
            base_url=settings.LITELLM_BASE_URL
        )
        self.sheets_service = SheetsService()

    def _call_gemini_with_backoff(self, messages):
        """
        Exponential backoff to handle 429 Rate Limits from the proxy.
        """
        max_retries = 5
        for attempt in range(max_retries):
            try:
                return self.client.chat.completions.create(
                    model=settings.MODEL_NAME,
                    messages=messages,
                    temperature=0.7
                )
            except (RateLimitError, APIError) as e:
                if attempt == max_retries - 1: raise e
                wait = (2 ** attempt) + 1
                print(f"SEO Agent: Rate limit hit. Retrying in {wait}s...")
                time.sleep(wait)

    def answer_question(self, query: str, spreadsheet_id: str = None):
        """
        Executes SEO analysis: Ingest Sheets -> Normalize -> Ground-truth Extraction -> AI Reasoning.
        """
        # Default to your specific SEO Audit Sheet
        sid = spreadsheet_id if spreadsheet_id else "1zzf4ax_H2WiTBVrJigGjF2Q3Yz-qy2qMCbAMKvl6VEE"
        
        try:
            # 1. Live data ingestion from Google Sheets using Service Account
            df = self.sheets_service.get_spreadsheet_data(sid)
            
            if df.empty:
                return "The SEO audit sheet appears to be empty or inaccessible. Please check permissions."

            # 2. Normalize schema to handle column variations (e.g., 'URL' vs 'Address')
            df = normalize_seo_dataframe(df)

            # 3. Extract ground-truth metrics to prevent AI hallucinations
            context = self._extract_audit_summary(df)

            # 4. Generate final insight with Gemini using specialized prompt
            return self._get_ai_reasoning(query, context)

        except Exception as e:
            return f"SEO Agent Error: {str(e)}"

    def _extract_audit_summary(self, df: pd.DataFrame):
        """
        Calculates hard numbers (status codes, indexability) before sending to LLM.
        """
        summary = {
            "total_urls": len(df),
            "indexability_status": df['indexability'].value_counts().to_dict() if 'indexability' in df.columns else {},
            "status_codes": df['status_code'].value_counts().to_dict() if 'status_code' in df.columns else {}
        }

        # Tier 2 Logic: HTTPS and Title Lengths
        if 'address' in df.columns:
            non_https = df[~df['address'].str.startswith('https', na=False)]
            summary["non_https_count"] = len(non_https)
            summary["non_https_samples"] = non_https['address'].head(3).tolist()

        if 'title_length' in df.columns:
            # Ensure numeric conversion for accurate filtering
            df['title_length'] = pd.to_numeric(df['title_length'], errors='coerce')
            long_titles = df[df['title_length'] > 60]
            summary["long_titles_count"] = len(long_titles)
            summary["long_titles_samples"] = long_titles[['address', 'title_length']].head(3).to_dict(orient='records')

        return summary

    def _get_ai_reasoning(self, query: str, context: dict):
        """
        Calls Gemini to explain technical SEO health based on the extracted data.
        """
        messages = [
            {"role": "system", "content": SEO_ANALYSIS_PROMPT},
            {"role": "user", "content": f"Audit Context: {json.dumps(context)}\n\nQuestion: {query}"}
        ]
        response = self._call_gemini_with_backoff(messages)
        return response.choices[0].message.content
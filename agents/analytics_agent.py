import json
import time
from datetime import datetime
from openai import OpenAI, RateLimitError, APIError
from core.config import settings
from core.prompts import GA4_PLANNER_PROMPT
from services.ga4_service import GA4Service

class AnalyticsAgent:
    def __init__(self):
        # LiteLLM points to the hackathon proxy
        self.client = OpenAI(
            api_key=settings.LITELLM_API_KEY,
            base_url=settings.LITELLM_BASE_URL
        )
        self.ga4_service = GA4Service()

    def _call_gemini_with_backoff(self, messages, json_mode=False):
        """
        Exponential backoff to handle 429 Rate Limits from LiteLLM proxy.
        """
        max_retries = 5
        for attempt in range(max_retries):
            try:
                # Configure structured output if requested
                response_format = None
                if json_mode:
                    response_format = {
                        "type": "json_object",
                        "response_schema": {
                            "type": "object",
                            "properties": {
                                "metrics": {"type": "array", "items": {"type": "string"}},
                                "dimensions": {"type": "array", "items": {"type": "string"}},
                                "date_ranges": {"type": "array", "items": {"type": "array", "minItems": 2, "maxItems": 2}},
                                "filters": {"type": "object"}
                            },
                            "required": ["metrics", "dimensions", "date_ranges"]
                        }
                    }

                return self.client.chat.completions.create(
                    model=settings.MODEL_NAME,
                    messages=messages,
                    response_format=response_format,
                    temperature=1.0  # Recommended for Gemini reasoning
                )
            except (RateLimitError, APIError) as e:
                # 429 is mapped to RateLimitError in OpenAI SDK
                if attempt == max_retries - 1: raise e
                wait = (2 ** attempt) + 1
                print(f"Rate limit hit. Retrying in {wait}s...")
                time.sleep(wait)

    def answer_question(self, query: str, property_id: str):
        """
        Full Tier 1 workflow: Reasoning -> Data Fetching -> Summarization.
        """
        try:
            # 1. Infer Reporting Plan (Metrics/Dimensions/Dates)
            reporting_plan = self._get_reporting_plan(query)
            
            # 2. Query Live GA4 Data API
            raw_data = self.ga4_service.run_analytics_report(property_id, reporting_plan)
            
            if "error" in raw_data:
                return f"I couldn't fetch the data: {raw_data['error']}"

            # 3. Summarize results in Natural Language
            return self._summarize_data(query, raw_data)
            
        except Exception as e:
            return f"Analytics Agent Error: {str(e)}"

    def _get_reporting_plan(self, query: str):
        """Uses Gemini to translate NL query into a GA4-compatible JSON plan."""
        today = datetime.now().strftime("%Y-%m-%d")
        
        response = self._call_gemini_with_backoff(
            messages=[
                {"role": "system", "content": GA4_PLANNER_PROMPT.format(today=today, query=query)},
                {"role": "user", "content": query}
            ],
            json_mode=True
        )
        return json.loads(response.choices[0].message.content)

    def _summarize_data(self, query: str, data: dict):
        """Fuses raw JSON data into a clear analyst summary."""
        response = self._call_gemini_with_backoff(
            messages=[
                {"role": "system", "content": "You are a professional Analytics Consultant. Summarize the following data into a clear, insightful answer. If the data is empty, explain that there is no traffic for this specific filter/period."},
                {"role": "user", "content": f"User Query: {query}\nRaw GA4 Data: {json.dumps(data)}"}
            ]
        )
        return response.choices[0].message.content
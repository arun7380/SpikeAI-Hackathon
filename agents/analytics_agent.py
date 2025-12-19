import json
import time
from datetime import datetime
from openai import OpenAI, RateLimitError, APIError
from core.config import settings
from core.prompts import GA4_PLANNER_PROMPT
from services.ga4_service import GA4Service
from tools.ga4_tools import GA4_REPORTING_TOOL_SCHEMA, validate_reporting_plan

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
                response_format = None
                if json_mode:
                    # Uses the structured schema from ga4_tools.py
                    response_format = {
                        "type": "json_object",
                        "response_schema": GA4_REPORTING_TOOL_SCHEMA["parameters"]
                    }

                return self.client.chat.completions.create(
                    model=settings.MODEL_NAME,
                    messages=messages,
                    response_format=response_format,
                    temperature=1.0
                )
            except (RateLimitError, APIError) as e:
                if attempt == max_retries - 1: raise e
                wait = (2 ** attempt) + 1
                print(f"Rate limit hit. Retrying in {wait}s...")
                time.sleep(wait)

    def answer_question(self, query: str, property_id: str = None):
        """
        Full Tier 1 workflow with Validation.
        """
        # Fallback to your hardcoded Property ID if none provided
        pid = property_id if property_id else "516810413"
        
        try:
            # 1. Infer Reporting Plan
            reporting_plan = self._get_reporting_plan(query)
            
            # 2. Server-side Validation
            # Ensures the LLM didn't hallucinate invalid metrics
            validate_reporting_plan(reporting_plan)
            
            # 3. Query Live GA4 Data API
            raw_data = self.ga4_service.run_analytics_report(pid, reporting_plan)
            
            if isinstance(raw_data, dict) and "error" in raw_data:
                return f"I couldn't fetch the data: {raw_data['error']}"

            # 4. Summarize results in Natural Language
            return self._summarize_data(query, raw_data)
            
        except ValueError as ve:
            return f"Validation Error: {str(ve)}"
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

    def _summarize_data(self, query: str, data: list):
        """Fuses raw JSON data into a clear analyst summary."""
        response = self._call_gemini_with_backoff(
            messages=[
                {"role": "system", "content": "You are a professional Analytics Consultant for Property 516810413. Summarize the data clearly. If data is empty, explain that there is no traffic for this period."},
                {"role": "user", "content": f"User Query: {query}\nRaw GA4 Data: {json.dumps(data)}"}
            ]
        )
        return response.choices[0].message.content
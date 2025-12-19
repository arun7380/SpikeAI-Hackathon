import json
import time
from openai import OpenAI, RateLimitError, APIError
from core.config import settings

class Aggregator:
    def __init__(self):
        # LiteLLM client for Gemini
        self.client = OpenAI(
            api_key=settings.LITELLM_API_KEY,
            base_url=settings.LITELLM_BASE_URL
        )

    def synthesize(self, query: str, agent_results: dict):
        """
        Fuses data from multiple agents into a single professional response.
        Requirement: Support Multi-agent routing and Data Fusion.
        """
        # If no data was returned by any agent, handle gracefully
        if not agent_results or all(v is None for v in agent_results.values()):
            return "I couldn't find enough data from the sources to answer your question."

        # System prompt for high-quality marketing synthesis
        system_prompt = """
        You are a Senior Marketing Data Scientist. 
        Your task is to FUSE data from GA4 (Analytics) and Screaming Frog (SEO) into one unified answer.
        
        RULES:
        1. If the user asks for a specific format (JSON/Table), follow it strictly.
        2. Correlate traffic metrics with technical SEO status (e.g., 'High traffic pages with long titles').
        3. Provide actionable insights based on the combined data.
        4. If one source provided no data, summarize what is available professionally.
        """

        try:
            # Use a retry loop for stability against 429 errors
            response = self._call_gemini_with_backoff(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Query: {query}\n\nAgent Results: {json.dumps(agent_results)}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Aggregator Error: Could not synthesize results. Raw results: {json.dumps(agent_results)}"

    def _call_gemini_with_backoff(self, messages):
        """Exponential backoff for the final synthesis step."""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return self.client.chat.completions.create(
                    model=settings.MODEL_NAME,
                    messages=messages,
                    temperature=0.7 # Slightly lower for more factual synthesis
                )
            except (RateLimitError, APIError) as e:
                if attempt == max_retries - 1: raise e
                time.sleep(2 ** attempt)
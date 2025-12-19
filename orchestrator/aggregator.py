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
        Fuses data from specialists into a professional response for Property 516810413.
        """
        if not agent_results or all(v is None for v in agent_results.values()):
            return "I couldn't find enough data from Property 516810413 or the SEO Sheet to answer your question."

        # Persona-driven system prompt for high-quality synthesis
        system_prompt = f"""
        You are a Senior Marketing Data Scientist. 
        Your goal is to provide a UNIFIED analysis for:
        - GA4 Property: 516810413
        - SEO Audit Sheet: 1zzf4ax_H2WiTBVrJigGjF2Q3Yz-qy2qMCbAMKvl6VEE
        
        DATA FUSION RULES:
        1. CORRELATION: Match traffic metrics (Analytics) with technical SEO health (Screaming Frog).
           Example: "The page /pricing has 0 traffic but is also marked as 'Non-Indexable' in the audit."
        2. STRUCTURE: Use bullet points for key findings and a 'Recommendations' section.
        3. INSIGHTS: Move beyond 'what happened' to 'why it matters' for this specific site.
        4. TRANSPARENCY: If data from one source is missing, explain it professionally.
        """

        try:
            # Final synthesis with specific temperature for factual accuracy
            response = self._call_gemini_with_backoff(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"User Query: {query}\n\nSpecialist Findings: {json.dumps(agent_results)}"}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Data Fusion Error: Could not synthesize findings. Results: {json.dumps(agent_results)}"

    def _call_gemini_with_backoff(self, messages):
        """Exponential backoff to handle proxy rate limits."""
        max_retries = 3
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
                time.sleep(wait)
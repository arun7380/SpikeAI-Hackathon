import json
from openai import OpenAI
from core.prompts import FINAL_AGGREGATOR_PROMPT
from core.config import settings

class Aggregator:
    def __init__(self):
        # Initialize LiteLLM client via provided proxy
        self.client = OpenAI(
            api_key=settings.LITELLM_API_KEY,
            base_url=settings.LITELLM_BASE_URL
        )

    async def aggregate(self, query: str, analytics_data: dict = None, seo_data: list = None):
        """
        Fuses data from multiple agents into a unified final response.
        Satisfies Tier 3 'Cross-agent data fusion' requirement.
        """
        
        # Prepare context for the LLM
        context = {
            "query": query,
            "analytics_results": analytics_data if analytics_data else "No analytics data fetched.",
            "seo_results": seo_data if seo_data else "No SEO data fetched."
        }

        try:
            # Call Gemini-1.5-flash to synthesize the final answer
            response = self.client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=[
                    {"role": "system", "content": FINAL_AGGREGATOR_PROMPT},
                    {"role": "user", "content": f"Context: {json.dumps(context)}"}
                ],
                temperature=0.2 # Lower temperature for factual accuracy
            )
            
            final_answer = response.choices[0].message.content
            return final_answer

        except Exception as e:
            # Handle sparse datasets gracefully as per requirements
            return f"I encountered an error while synthesizing the final answer: {str(e)}"

    def format_as_json(self, combined_data: dict):
        """
        Helper to return strict JSON when explicitly requested (Tier 2/3 requirement).
        """
        return json.dumps(combined_data, indent=2)
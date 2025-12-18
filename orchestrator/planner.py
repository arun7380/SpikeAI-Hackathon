import json
from openai import OpenAI
from core.prompts import ANALYTICS_PLANNER_PROMPT, SEO_AGENT_PROMPT
from core.config import settings

class Planner:
    def __init__(self):
        # Using LiteLLM proxy as the unified API format [cite: 245, 250]
        self.client = OpenAI(
            api_key=settings.LITELLM_API_KEY,
            base_url=settings.LITELLM_BASE_URL
        )

    async def create_plan(self, query: str, intent: str):
        """
        Decomposes the query into tasks for specific agents[cite: 31].
        """
        if intent == "analytics":
            return await self._plan_analytics(query)
        elif intent == "seo":
            return await self._plan_seo(query)
        elif intent == "fusion":
            return await self._plan_fusion(query)
        else:
            raise ValueError(f"Unknown intent type for planning: {intent}")

    async def _plan_analytics(self, query: str):
        """
        Infers metrics, dimensions, and date ranges for GA4[cite: 73, 179].
        """
        response = self.client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": ANALYTICS_PLANNER_PROMPT},
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"} # Ensures machine-readable output [cite: 58]
        )
        return json.loads(response.choices[0].message.content)

    async def _plan_seo(self, query: str):
        """
        Infers filtering and aggregation logic for SEO data[cite: 61, 64, 90].
        """
        response = self.client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": SEO_AGENT_PROMPT},
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    async def _plan_fusion(self, query: str):
        """
        Decomposes complex questions into multi-step cross-agent tasks[cite: 31, 99].
        Example: 'What are the top 10 pages and their titles?' [cite: 136]
        """
        fusion_instruction = (
            "Break this query into two parts: "
            "1. Analytics task (Metrics/Dimensions/Dates) "
            "2. SEO task (Columns to fetch/Filter logic). "
            "Return as a JSON with keys 'analytics_step' and 'seo_step'."
        )
        
        response = self.client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": fusion_instruction},
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
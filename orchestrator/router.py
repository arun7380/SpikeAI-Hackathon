import json
from openai import OpenAI
from core.config import settings
from core.prompts import ORCHESTRATOR_ROUTER_PROMPT
from orchestrator.planner import Planner
from orchestrator.aggregator import Aggregator
from agents.analytics_agent import AnalyticsAgent
from agents.seo_agent import SEOAgent

class Orchestrator:
    def __init__(self):
        # Unified API format via LiteLLM proxy [cite: 242, 245]
        self.client = OpenAI(
            api_key=settings.LITELLM_API_KEY,
            base_url=settings.LITELLM_BASE_URL
        )
        self.planner = Planner()
        self.aggregator = Aggregator()
        self.analytics_agent = AnalyticsAgent()
        self.seo_agent = SEOAgent()

    async def route_query(self, query: str, property_id: str = None):
        """
        Main orchestration logic: Detect intent -> Create Plan -> Execute -> Aggregate.
        """
        # 1. Intent Detection [cite: 29, 97]
        intent_data = await self._get_intent(query)
        intent = intent_data.get("intent")

        # 2. Routing logic [cite: 30, 98]
        if intent == "analytics":
            if not property_id:
                raise ValueError("propertyId is required for GA4 analytics queries.") # [cite: 107]
            
            # Tier 1 flow: Analytics Agent
            plan = await self.planner.create_plan(query, "analytics")
            data = await self.analytics_agent.run(plan, property_id)
            return await self.aggregator.aggregate(query, analytics_data=data)

        elif intent == "seo":
            # Tier 2 flow: SEO Agent
            plan = await self.planner.create_plan(query, "seo")
            data = await self.seo_agent.run(plan)
            return await self.aggregator.aggregate(query, seo_data=data)

        elif intent == "fusion":
            # Tier 3 flow: Multi-Agent Data Fusion [cite: 99, 135]
            fusion_plan = await self.planner.create_plan(query, "fusion")
            
            # Parallel or sequential execution
            ga4_results = await self.analytics_agent.run(fusion_plan["analytics_step"], property_id)
            seo_results = await self.seo_agent.run(fusion_plan["seo_step"])
            
            # Unified response aggregation 
            return await self.aggregator.aggregate(query, analytics_data=ga4_results, seo_data=seo_results)

        else:
            return "I'm sorry, I couldn't determine the intent of your request. Please try again."

    async def _get_intent(self, query: str):
        """
        Uses LiteLLM to classify the query into Analytics, SEO, or Fusion.
        """
        response = self.client.chat.completions.create(
            model=settings.MODEL_NAME, # Defaults to gemini-1.5-flash [cite: 256]
            messages=[
                {"role": "system", "content": ORCHESTRATOR_ROUTER_PROMPT},
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)
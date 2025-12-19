import json
from openai import OpenAI
from core.config import settings
from core.prompts import ORCHESTRATOR_ROUTER_PROMPT
from agents.analytics_agent import AnalyticsAgent
from agents.seo_agent import SEOAgent
from orchestrator.planner import Planner
from orchestrator.aggregator import Aggregator

class Orchestrator:
    def __init__(self):
        # LiteLLM Proxy Client
        self.client = OpenAI(
            api_key=settings.LITELLM_API_KEY,
            base_url=settings.LITELLM_BASE_URL
        )
        
        # Initialize Specialist Agents
        self.analytics_agent = AnalyticsAgent()
        self.seo_agent = SEOAgent()
        
        # Initialize Orchestration Components
        self.planner = Planner()
        self.aggregator = Aggregator()

    def route_and_execute(self, query: str, property_id: str = None, spreadsheet_id: str = None):
        """
        Main entry point for the backend. Handles routing, execution, and fusion.
        """
        try:
            # 1. Intent Detection: Determine which domains are involved
            intent_data = self._get_intent(query)
            intent = intent_data.get("intent", "analytics")
            
            # 2. Tier 3: Multi-Agent Planning & Execution
            if intent == "both":
                return self._handle_multi_agent_fusion(query, property_id, spreadsheet_id)
            
            # 3. Tier 1 & 2: Single Agent Routing
            if intent == "analytics":
                if not property_id:
                    return "Error: propertyId is required for GA4 queries."
                return self.analytics_agent.answer_question(query, property_id)
            
            if intent == "seo":
                return self.seo_agent.answer_question(query, spreadsheet_id)

        except Exception as e:
            print(f"Orchestration Error: {str(e)}")
            return f"I encountered an error while processing your request: {str(e)}"

    def _get_intent(self, query: str):
        """Uses Gemini to detect if the query is GA4, SEO, or Both."""
        response = self.client.chat.completions.create(
            model=settings.MODEL_NAME,
            messages=[
                {"role": "system", "content": ORCHESTRATOR_ROUTER_PROMPT},
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    def _handle_multi_agent_fusion(self, query: str, property_id: str, spreadsheet_id: str):
        """
        Tier 3 Logic: Plan tasks, execute sequentially, and aggregate.
        """
        # Create an execution plan (Task Decomposition)
        plan = self.planner.create_execution_plan(query)
        agent_results = {}

        for task in plan.get("tasks", []):
            agent_type = task.get("agent")
            
            if agent_type == "Analytics_Agent":
                agent_results["analytics"] = self.analytics_agent.answer_question(
                    task.get("description"), property_id
                )
            elif agent_type == "SEO_Agent":
                # Pass previous results if 'requires_context' is true
                agent_results["seo"] = self.seo_agent.answer_question(
                    task.get("description"), spreadsheet_id
                )

        # Final Response Aggregation (Data Fusion)
        return self.aggregator.synthesize(query, agent_results)
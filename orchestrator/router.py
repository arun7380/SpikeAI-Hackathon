import json
import time
from openai import OpenAI, RateLimitError, APIError
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

    def _call_gemini_with_backoff(self, messages):
        """
        Internal backoff for the router to handle high concurrency during the hackathon.
        """
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return self.client.chat.completions.create(
                    model=settings.MODEL_NAME,
                    messages=messages,
                    response_format={"type": "json_object"}
                )
            except (RateLimitError, APIError):
                if attempt == max_retries - 1: raise
                time.sleep((2 ** attempt) + 1)

    def route_and_execute(self, query: str, property_id: str = None, spreadsheet_id: str = None):
        """
        Main entry point. Automatically injects default IDs if missing.
        """
        # Inject Hackathon Defaults
        pid = property_id if property_id else "516810413"
        sid = spreadsheet_id if spreadsheet_id else "1zzf4ax_H2WiTBVrJigGjF2Q3Yz-qy2qMCbAMKvl6VEE"

        try:
            # 1. Intent Detection
            intent_data = self._get_intent(query)
            intent = intent_data.get("intent", "analytics")
            
            # 2. Tier 3: Multi-Agent Fusion
            if intent == "both":
                return self._handle_multi_agent_fusion(query, pid, sid)
            
            # 3. Tier 1: Analytics Specialist
            if intent == "analytics":
                return self.analytics_agent.answer_question(query, pid)
            
            # 4. Tier 2: SEO Specialist
            if intent == "seo":
                return self.seo_agent.answer_question(query, sid)

        except Exception as e:
            return f"Orchestration Error: {str(e)}"

    def _get_intent(self, query: str):
        """Uses Gemini to detect if the query is GA4, SEO, or Both."""
        messages = [
            {"role": "system", "content": ORCHESTRATOR_ROUTER_PROMPT},
            {"role": "user", "content": query}
        ]
        response = self._call_gemini_with_backoff(messages)
        return json.loads(response.choices[0].message.content)

    def _handle_multi_agent_fusion(self, query: str, pid: str, sid: str):
        """
        Tier 3 Logic: Sequential task execution with context sharing.
        """
        plan = self.planner.create_execution_plan(query)
        agent_results = {}

        for task in plan.get("tasks", []):
            agent_type = task.get("agent")
            desc = task.get("description")
            
            if agent_type == "Analytics_Agent":
                agent_results["analytics"] = self.analytics_agent.answer_question(desc, pid)
            elif agent_type == "SEO_Agent":
                agent_results["seo"] = self.seo_agent.answer_question(desc, sid)

        # Data Fusion: Aggregator synthesizes the specialist findings
        return self.aggregator.synthesize(query, agent_results)
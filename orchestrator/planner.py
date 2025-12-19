import json
from datetime import datetime
from typing import List, Dict
from openai import OpenAI
from core.config import settings

class Planner:
    def __init__(self):
        # Using LiteLLM Proxy for Gemini access
        self.client = OpenAI(
            api_key=settings.LITELLM_API_KEY,
            base_url=settings.LITELLM_BASE_URL
        )

    def create_execution_plan(self, query: str) -> Dict:
        """
        Decomposes a NL query into a sequence of actionable agent tasks.
        Ensures logical order and dependency awareness.
        """
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Defining the schema for strict JSON compliance
        response_schema = {
            "type": "object",
            "properties": {
                "plan_name": {"type": "string"},
                "tasks": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "id": {"type": "integer"},
                            "agent": {"type": "string", "enum": ["Analytics_Agent", "SEO_Agent"]},
                            "description": {"type": "string"},
                            "requires_context_from": {"type": "integer", "nullable": True},
                            "goal": {"type": "string"}
                        },
                        "required": ["id", "agent", "description", "goal"]
                    }
                }
            },
            "required": ["plan_name", "tasks"]
        }

        system_prompt = f"""
        You are a Strategic Planner for a Multi-Agent Marketing AI.
        Break the user query into a sequence of executable subtasks.
        
        AVAILABLE AGENTS:
        1. Analytics_Agent: Queries GA4 for traffic, users, and page metrics.
        2. SEO_Agent: Queries Screaming Frog data for titles, status codes, and technical health.
        
        RULES:
        - Identify if a task depends on the output of a previous task (e.g., fetching SEO data for URLs found by Analytics).
        - Ensure logical sequencing (Search/Filter first, then Analyze).
        """

        try:
            response = self.client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Today is {today}. Query: {query}"}
                ],
                response_format={"type": "json_object", "response_schema": response_schema}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Planning Error: {str(e)}")
            # Fallback to a single-step plan if logic fails
            return {
                "plan_name": "Fallback Plan",
                "tasks": [{"id": 1, "agent": "Analytics_Agent", "description": query, "goal": "Answer query"}]
            }
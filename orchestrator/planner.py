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
        Targets specific Hackathon IDs: GA4 (516810413) and Sheets (1zzf4ax...).
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

        # Strategic prompt updated with your specific Property and Sheet IDs
        system_prompt = f"""
        You are a Strategic Planner for a Multi-Agent Marketing AI.
        Break the user query into a sequence of executable subtasks.

        GROUND TRUTH IDENTIFIERS:
        - GA4 Property ID: 516810413
        - SEO Audit Sheet ID: 1zzf4ax_H2WiTBVrJigGjF2Q3Yz-qy2qMCbAMKvl6VEE

        AVAILABLE AGENTS:
        1. Analytics_Agent: Queries GA4 (Property 516810413) for traffic and user metrics.
        2. SEO_Agent: Queries Screaming Frog data (Sheet 1zzf4ax...) for technical health.
        
        RULES:
        - Identify if a task depends on the output of a previous task.
        - Ensure logical sequencing (e.g., fetch non-indexable URLs from SEO first, then check their traffic in Analytics).
        - Always reference the Ground Truth IDs in your task descriptions.
        """

        try:
            response = self.client.chat.completions.create(
                model=settings.MODEL_NAME,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Today is {today}. Query: {query}"}
                ],
                # Force structured output using your schema
                response_format={"type": "json_object", "response_schema": response_schema}
            )
            
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            print(f"Planning Error: {str(e)}")
            # Fallback to a single-step plan targeting your default IDs
            return {
                "plan_name": "Fallback Strategic Plan",
                "tasks": [{"id": 1, "agent": "Analytics_Agent", "description": f"Analyze traffic for {query} on Property 516810413", "goal": "Resolve user query"}]
            }
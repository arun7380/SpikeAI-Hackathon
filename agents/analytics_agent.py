import json
from openai import OpenAI
from core.prompts import ANALYTICS_AGENT_PROMPT
from services.ga4_service import GA4Service

class AnalyticsAgent:
    def __init__(self, api_key: str, base_url: str):
        # Initialize the LiteLLM client as recommended [cite: 271, 276]
        self.llm_client = OpenAI(api_key=api_key, base_url=base_url)
        self.ga4_service = GA4Service()

    async def run(self, query: str, property_id: str):
        """
        Executes the Tier 1 Analytics Agent logic[cite: 68].
        """
        # 1. Inference: Convert NL to a GA4 Reporting Plan [cite: 50]
        # Includes metrics, dimensions, and date ranges [cite: 76, 77, 78]
        reporting_plan = self._generate_reporting_plan(query)
        
        # 2. Validation: Server-side check of GA4 fields [cite: 79, 180]
        self._validate_plan(reporting_plan)

        # 3. Execution: Fetch live data using the provided propertyId [cite: 38, 73]
        raw_data = self.ga4_service.query(
            property_id=property_id,
            metrics=reporting_plan.get("metrics"),
            dimensions=reporting_plan.get("dimensions"),
            date_ranges=reporting_plan.get("date_ranges")
        )

        # 4. Aggregation: Summarize data into natural language [cite: 80, 186]
        return self._summarize_results(query, raw_data)

    def _generate_reporting_plan(self, query: str):
        # Calls gemini-1.5-flash via LiteLLM [cite: 256, 267]
        response = self.llm_client.chat.completions.create(
            model="gemini-1.5-flash",
            messages=[
                {"role": "system", "content": ANALYTICS_AGENT_PROMPT},
                {"role": "user", "content": query}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    def _validate_plan(self, plan: dict):
        # Implementation of server-side validation against an allowlist 
        allowed_metrics = ["activeUsers", "sessions", "screenPageViews"] # [cite: 176]
        for m in plan.get("metrics", []):
            if m not in allowed_metrics:
                raise ValueError(f"Unauthorized metric: {m}")

    def _summarize_results(self, query: str, data: dict):
        # Final pass to turn raw numbers into a clear explanation [cite: 58, 186]
        # If the dataset is empty, handle it gracefully [cite: 57, 183]
        if not data:
            return "The query returned no data for the specified period."
        
        # LLM call to synthesize the final answer
        summary_response = self.llm_client.chat.completions.create(
            model="gemini-1.5-flash",
            messages=[
                {"role": "system", "content": "Summarize the following GA4 data for the user."},
                {"role": "user", "content": f"Query: {query}\nData: {json.dumps(data)}"}
            ]
        )
        return summary_response.choices[0].message.content
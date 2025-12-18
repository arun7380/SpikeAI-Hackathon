import json
from openai import OpenAI
from services.sheets_service import SheetsService
from core.prompts import SEO_AGENT_PROMPT

class SEOAgent:
    def __init__(self, api_key: str, base_url: str):
        # Initialize the LiteLLM client as specified in assets [cite: 17, 250]
        self.llm_client = OpenAI(api_key=api_key, base_url=base_url)
        self.sheets_service = SheetsService()

    async def run(self, query: str):
        """
        Executes Tier 2 SEO Agent logic: Live ingestion and reasoning[cite: 86, 89].
        """
        # 1. Fetch live data from the Screaming Frog Google Sheet 
        # This ensures we use a live data source, not a static export [cite: 9]
        raw_seo_data = self.sheets_service.get_spreadsheet_data()

        # 2. Reasoning: Use LLM to determine the filtering/aggregation plan
        # The agent must infer conditional logic from NL [cite: 65, 90]
        execution_plan = self._generate_execution_plan(query, raw_seo_data[0]) # Pass headers for schema awareness

        # 3. Execution: Apply logic (Filtering, Grouping, Aggregations) [cite: 61, 63, 64]
        processed_data = self._execute_logic(execution_plan, raw_seo_data)

        # 4. Response Generation: Return natural language or strict JSON [cite: 58, 91]
        return self._format_response(query, processed_data)

    def _generate_execution_plan(self, query: str, headers: list):
        """
        Translates NL to a JSON plan: e.g., {'filter': {'Address': 'not starts_with https'}} [cite: 93]
        """
        response = self.llm_client.chat.completions.create(
            model="gemini-1.5-flash",
            messages=[
                {"role": "system", "content": SEO_AGENT_PROMPT},
                {"role": "user", "content": f"Headers: {headers}\nQuery: {query}"}
            ],
            response_format={"type": "json_object"}
        )
        return json.loads(response.choices[0].message.content)

    def _execute_logic(self, plan: dict, data: list):
        """
        Handles schema changes safely by mapping logical intent to available headers.
        """
        # Logic to iterate through rows and apply filters like 'Title 1 length > 60' 
        # Example: filtered_rows = [row for row in data if len(row['Title 1']) > 60]
        pass 

    def _format_response(self, query: str, data: list):
        """
        Summarizes SEO insights (e.g., assessing technical health)[cite: 133].
        """
        # Synthesize final answer based on the processed data [cite: 80, 100]
        pass
import os
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    OrderBy,
    FilterExpression,
    Filter
)
from core.config import settings

class GA4Service:
    def __init__(self):
        """
        Initializes the GA4 Client.
        Requirement: Load credentials from credentials.json at runtime.
        """
        # Set the environment variable so the Google library finds the file
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GA4_CREDENTIALS_PATH
        self.client = BetaAnalyticsDataClient()

    def run_analytics_report(self, property_id: str, plan: dict):
        """
        Executes a report request against the GA4 Data API.
        
        :param property_id: Provided in the API request body.
        :param plan: Dict containing metrics, dimensions, and date_ranges.
        """
        try:
            # Construct metrics and dimensions objects
            metrics = [Metric(name=m) for m in plan.get("metrics", [])]
            dimensions = [Dimension(name=d) for d in plan.get("dimensions", [])]
            
            # Construct date ranges (expects list of tuples/lists: [['start', 'end']])
            date_ranges = [
                DateRange(start_date=dr[0], end_date=dr[1]) 
                for dr in plan.get("date_ranges", [])
            ]

            # Build the request
            request = RunReportRequest(
                property=f"properties/{property_id}",
                dimensions=dimensions,
                metrics=metrics,
                date_ranges=date_ranges,
            )

            # Optional: Add dimension filters if the LLM provided them
            if plan.get("filters"):
                # Simplified example: matching a specific page path
                f = plan["filters"]
                request.dimension_filter = FilterExpression(
                    filter=Filter(
                        field_name=f["dimension"],
                        string_filter=Filter.StringFilter(value=f["value"])
                    )
                )

            # Execute the request
            response = self.client.run_report(request)
            return self._parse_response(response)

        except Exception as e:
            # Requirement: Handle empty/sparse datasets and errors gracefully.
            return {"error": str(e), "status": "failed"}

    def _parse_response(self, response):
        """
        Converts the complex GA4 response object into a simple list of dicts.
        """
        results = []
        for row in response.rows:
            row_data = {}
            # Extract dimension values
            for i, dimension_value in enumerate(row.dimension_values):
                dimension_name = response.dimension_headers[i].name
                row_data[dimension_name] = dimension_value.value
            
            # Extract metric values
            for i, metric_value in enumerate(row.metric_values):
                metric_name = response.metric_headers[i].name
                row_data[metric_name] = metric_value.value
            
            results.append(row_data)
        
        return {
            "data": results,
            "row_count": response.row_count,
            "metadata": "No data found for this period" if not results else "Success"
        }
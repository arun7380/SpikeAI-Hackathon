import os
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import (
    DateRange,
    Dimension,
    Metric,
    RunReportRequest,
    OrderBy
)
from core.config import settings

class GA4Service:
    def __init__(self):
        """
        Initializes the client using the credentials.json file at project root.
        Requirement: Must work without code changes after replacement.
        """
        # Load credentials directly from the path defined in settings
        self.client = BetaAnalyticsDataClient.from_service_account_json(
            str(settings.CREDENTIALS_JSON_PATH)
        )

    def query(self, property_id: str, metrics: list, dimensions: list, date_ranges: list):
        """
        Executes a runReport request against the specified GA4 property.
        """
        # Construct the metrics list using GA4 types
        ga4_metrics = [Metric(name=m) for m in metrics]
        
        # Construct the dimensions list
        ga4_dimensions = [Dimension(name=d) for d in dimensions]
        
        # Construct date ranges (expects strings like '2023-01-01' or '30daysAgo')
        ga4_date_ranges = [
            DateRange(start_date=date_ranges[0], end_date=date_ranges[1])
        ]

        # Build the request object
        request = RunReportRequest(
            property=f"properties/{property_id}",
            dimensions=ga4_dimensions,
            metrics=ga4_metrics,
            date_ranges=ga4_date_ranges,
        )

        try:
            # Execute live data pull
            response = self.client.run_report(request)
            return self._parse_response(response)
        except Exception as e:
            # Requirements: Handle errors gracefully and return structured info
            return {"error": str(e), "data": []}

    def _parse_response(self, response):
        """
        Converts the raw API response into a simplified dictionary format.
        """
        results = []
        
        # Extract dimension names and metric names for headers
        dim_headers = [header.name for header in response.dimension_headers]
        metric_headers = [header.name for header in response.metric_headers]

        # Iterate through rows and build a clean data list
        for row in response.rows:
            row_data = {}
            for i, val in enumerate(row.dimension_values):
                row_data[dim_headers[i]] = val.value
            for i, val in enumerate(row.metric_values):
                row_data[metric_headers[i]] = val.value
            results.append(row_data)

        return {
            "row_count": response.row_count,
            "data": results,
            "metadata": {
                "currency_code": response.metadata.currency_code,
                "time_zone": response.metadata.time_zone
            }
        }
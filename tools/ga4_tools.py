"""
tools/ga4_tools.py - Schema and validation for GA4 reporting tools.
"""

# Allowed values to prevent LLM hallucinations
VALID_METRICS = [
    "activeUsers", "sessions", "screenPageViews", 
    "engagementRate", "averageEngagementTime", "eventCount",
    "conversions", "totalRevenue", "bounceRate"
]

VALID_DIMENSIONS = [
    "pagePath", "pageTitle", "date", "sessionSource", 
    "sessionMedium", "country", "city", "deviceCategory",
    "landingPage", "channelGroup"
]

# This schema tells Gemini exactly how to format the tool output
GA4_REPORTING_TOOL_SCHEMA = {
    "name": "run_ga4_report",
    "description": "Fetch live website analytics data from Google Analytics 4.",
    "parameters": {
        "type": "object",
        "properties": {
            "metrics": {
                "type": "array",
                "items": {"type": "string", "enum": VALID_METRICS},
                "description": "The quantitative measurements to fetch (e.g., sessions)."
            },
            "dimensions": {
                "type": "array",
                "items": {"type": "string", "enum": VALID_DIMENSIONS},
                "description": "The attributes to group data by (e.g., pagePath)."
            },
            "date_ranges": {
                "type": "array",
                "items": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 2, "maxItems": 2
                },
                "description": "List of [start_date, end_date] in YYYY-MM-DD format."
            },
            "filters": {
                "type": "object",
                "properties": {
                    "dimension": {"type": "string"},
                    "value": {"type": "string"}
                },
                "description": "Optional dimension filter (e.g., filter by specific page path)."
            }
        },
        "required": ["metrics", "dimensions", "date_ranges"]
    }
}

def validate_reporting_plan(plan: dict):
    """
    Server-side validation of GA4 fields before calling the API.
    Required for Tier 1 Production Readiness.
    """
    for m in plan.get("metrics", []):
        if m not in VALID_METRICS:
            raise ValueError(f"Invalid metric: {m}")
            
    for d in plan.get("dimensions", []):
        if d not in VALID_DIMENSIONS:
            raise ValueError(f"Invalid dimension: {d}")
            
    return True
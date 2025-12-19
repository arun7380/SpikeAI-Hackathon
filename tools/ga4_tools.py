"""
tools/ga4_tools.py - Schema and validation for GA4 reporting tools.
"""

# Hardcoded Property ID for Property: 516810413
DEFAULT_PROPERTY_ID = "516810413"

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
    "description": "Fetch live website analytics data from Google Analytics 4 for Property 516810413.",
    "parameters": {
        "type": "object",
        "properties": {
            "property_id": {
                "type": "string",
                "default": DEFAULT_PROPERTY_ID,
                "description": "The GA4 Property ID to query."
            },
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
                    "dimension": {"type": "string", "enum": VALID_DIMENSIONS},
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
    Ensures Tier 1 Production Readiness by blocking invalid requests.
    """
    # Validate Property ID
    p_id = plan.get("property_id", DEFAULT_PROPERTY_ID)
    if not p_id.isdigit():
        raise ValueError(f"Invalid Property ID format: {p_id}")

    # Validate Metrics
    for m in plan.get("metrics", []):
        if m not in VALID_METRICS:
            raise ValueError(f"Invalid or unsupported metric: {m}")
            
    # Validate Dimensions
    for d in plan.get("dimensions", []):
        if d not in VALID_DIMENSIONS:
            raise ValueError(f"Invalid or unsupported dimension: {d}")
            
    return True
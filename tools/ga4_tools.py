from services.ga4_service import GA4Service
import logging

logger = logging.getLogger(__name__)
ga4_service = GA4Service()

def get_traffic_overview(property_id: str, date_range: list):
    """
    Fetches a high-level overview of traffic including users and sessions.
    Args:
        property_id: The GA4 Property ID.
        date_range: A list [start_date, end_date], e.g., ["30daysAgo", "yesterday"].
    """
    metrics = ["activeUsers", "sessions", "screenPageViews"]
    dimensions = ["date"] # Group by date for a time-series overview
    
    logger.info(f"Tool: Fetching traffic overview for {property_id}")
    return ga4_service.query(property_id, metrics, dimensions, date_range)

def get_page_performance(property_id: str, date_range: list, limit: int = 10):
    """
    Fetches the top performing pages by views.
    Args:
        property_id: The GA4 Property ID.
        date_range: A list [start_date, end_date].
        limit: Number of pages to return.
    """
    metrics = ["screenPageViews", "sessions"]
    dimensions = ["pagePath"]
    
    logger.info(f"Tool: Fetching top {limit} pages for {property_id}")
    result = ga4_service.query(property_id, metrics, dimensions, date_range)
    
    # Simple top-N slice if the API returns more
    if "data" in result:
        result["data"] = result["data"][:limit]
    return result

def get_user_demographics(property_id: str, date_range: list):
    """
    Analyzes user traffic by device category and country.
    """
    metrics = ["activeUsers"]
    dimensions = ["deviceCategory", "country"]
    
    logger.info(f"Tool: Fetching demographics for {property_id}")
    return ga4_service.query(property_id, metrics, dimensions, date_range)
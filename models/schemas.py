from pydantic import BaseModel, Field
from typing import Optional, Any, List, Dict

class QueryRequest(BaseModel):
    """
    Validation schema for the single POST /query endpoint.
    """
    # Required natural language question
    query: str = Field(
        ..., 
        description="The natural language question from the user",
        examples=["How many users visited the pricing page in the last 14 days?"]
    )
    
    # Required for GA4 queries, optional for others
    propertyId: Optional[str] = Field(
        None, 
        description="The GA4 Property ID (Required for analytics queries)",
        examples=["123456789"]
    )

class QueryResponse(BaseModel):
    """
    Structured response format for the API.
    Provides clear natural-language explanations.
    """
    answer: str = Field(..., description="The synthesized natural language response")
    
    # Optional field to provide strict JSON when explicitly requested
    data: Optional[Dict[str, Any]] = Field(
        None, 
        description="Structured data results if JSON output was requested"
    )

class GA4ReportingPlan(BaseModel):
    """
    Internal schema for the Analytics Agent's execution plan.
    """
    metrics: List[str] # e.g., activeUsers, sessions
    dimensions: List[str] # e.g., pagePath, date
    date_ranges: List[str] # e.g., ["30daysAgo", "yesterday"]
    filters: Optional[List[Dict[str, Any]]] = None
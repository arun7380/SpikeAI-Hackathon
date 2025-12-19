import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import logging

# Internal imports from your project structure
from orchestrator.router import Orchestrator
from core.config import settings

# Configure logging for production readiness
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Spike AI Analytics Backend",
    description="Production-ready API for GA4 and SEO natural language queries.",
    version="1.0.0"
)

# Initialize the central Orchestrator (singleton pattern)
orchestrator = Orchestrator()

# --- Request & Response Schemas ---
class QueryRequest(BaseModel):
    """
    Strictly adheres to the Hackathon API Contract.
    """
    query: str = Field(..., description="Natural language question from the user.")
    propertyId: Optional[str] = Field(None, description="Required for GA4-related queries.")
    # spreadsheetId is added here to allow the agent to know which SEO sheet to audit
    spreadsheetId: Optional[str] = Field(None, description="ID of the Google Sheet containing SEO data.")

class QueryResponse(BaseModel):
    response: str

# --- API Endpoints ---
@app.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    """
    The only interface used for evaluation. 
    Accepts JSON input and returns natural-language explanations.
    """
    logger.info(f"Received query: {request.query} for Property: {request.propertyId}")

    if not request.query.strip():
        raise HTTPException(status_code=400, detail="The 'query' field cannot be empty.")

    try:
        # Pass request to the Orchestrator for Intent Detection and Agent Routing
        final_answer = orchestrator.route_and_execute(
            query=request.query,
            property_id=request.propertyId,
            spreadsheet_id=request.spreadsheetId
        )
        
        return QueryResponse(response=final_answer)

    except Exception as e:
        logger.error(f"Execution Error: {str(e)}")
        # Requirement: Handle errors gracefully and return clear explanations
        raise HTTPException(
            status_code=500, 
            detail="An internal error occurred while processing your request."
        )

# --- Server Lifecycle ---
if __name__ == "__main__":
    # MANDATORY: Application must bind only to port 8080
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "api.server:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=False  # Set to False for production/evaluation
    )
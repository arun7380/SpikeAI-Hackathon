import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import logging

# Internal imports
from orchestrator.router import Orchestrator
from core.config import settings

# Configure logging for production observability
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Spike AI Analytics Backend",
    description="Production-ready API for GA4 and SEO natural language queries.",
    version="1.0.0"
)

# Initialize Orchestrator as a singleton
orchestrator = Orchestrator()

# --- Request & Response Schemas ---
class QueryRequest(BaseModel):
    """
    Strictly adheres to the Hackathon API Contract.
    Includes fallback logic for Property and Sheet IDs.
    """
    query: str = Field(..., description="Natural language question from the user.")
    
    # Optional fields with internal hardcoded fallbacks
    propertyId: Optional[str] = Field(
        default=None, 
        description="GA4 Property ID. Defaults to 516810413 if omitted."
    )
    spreadsheetId: Optional[str] = Field(
        default=None, 
        description="Google Sheet ID for SEO data. Defaults to 1zzf4ax... if omitted."
    )

class QueryResponse(BaseModel):
    response: str

# --- API Endpoints ---
@app.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    """
    Main evaluation endpoint. 
    Routes requests through the Orchestrator to specialized agents.
    """
    logger.info(f"Processing query: '{request.query}'")

    if not request.query.strip():
        raise HTTPException(status_code=400, detail="The 'query' field cannot be empty.")

    try:
        # Pass request to the Orchestrator
        # The Orchestrator will use your team's IDs if the request fields are None
        final_answer = orchestrator.route_and_execute(
            query=request.query,
            property_id=request.propertyId,
            spreadsheet_id=request.spreadsheetId
        )
        
        return QueryResponse(response=final_answer)

    except Exception as e:
        logger.error(f"Execution Error: {str(e)}", exc_info=True)
        # Graceful error handling for hackathon evaluation
        raise HTTPException(
            status_code=500, 
            detail="The AI encountered an issue processing your data. Please check your credentials.json."
        )

# --- Server Lifecycle ---
if __name__ == "__main__":
    # MANDATORY: Application must bind only to port 8080
    logger.info(f"Starting Spike AI Server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "api.server:app", 
        host=settings.HOST, 
        port=settings.PORT, 
        reload=False 
    )
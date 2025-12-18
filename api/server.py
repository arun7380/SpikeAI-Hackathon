import uvicorn
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from models.schemas import QueryRequest, QueryResponse
from orchestrator.router import Orchestrator
import logging

# Set up structured logging for production realism
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Spike AI Multi-Agent Backend",
    description="Unified API for Web Analytics (GA4) and SEO Audit (Screaming Frog)",
    version="1.0.0"
)

# Initialize the Orchestrator (Intent Detection & Routing)
orchestrator = Orchestrator()

@app.post("/query", response_model=QueryResponse)
async def handle_query(request: QueryRequest):
    """
    Main entry point for all hackathon queries.
    Evaluates: Intent detection, routing, and final answer synthesis.
    """
    logger.info(f"Received query: {request.query} | PropertyID: {request.propertyId}")

    try:
        # Pass control to the orchestrator to route between Analytics and SEO agents
        result = await orchestrator.route_query(
            query=request.query, 
            property_id=request.propertyId
        )
        return QueryResponse(answer=result)
        
    except ValueError as ve:
        # Handle known domain errors (e.g., missing propertyId for GA4)
        logger.warning(f"Validation Error: {str(ve)}")
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        # Catch-all for unexpected errors to ensure the system doesn't crash
        logger.error(f"System Error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred while processing the agent reasoning.")

# Custom health check (Best practice for production-ready backends)
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    # MANDATORY: Application must bind to port 8080 for evaluation
    uvicorn.run(app, host="0.0.0.0", port=8080)
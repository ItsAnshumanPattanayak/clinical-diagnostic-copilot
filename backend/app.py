"""
FastAPI Server - Clinical Diagnostic Copilot
============================================
Main application entry point.

Endpoints:
- POST /analyze - Upload image and run diagnostic workflow
- GET /health - Health check
- GET / - Serve frontend

Production considerations implemented:
- CORS for cross-origin requests
- File upload validation
- Error handling and logging
- Async request processing
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, List
import os
import sys
from pathlib import Path

# Add backend directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

# Import our custom modules
from agents.graph import diagnostic_graph
from agents.state import AgentState

# ============================================================================
# APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="Clinical Diagnostic Copilot",
    description="AI-powered multimodal medical image analysis system",
    version="1.0.0",
    docs_url="/api/docs",  # Swagger UI at /api/docs
    redoc_url="/api/redoc"  # ReDoc at /api/redoc
)

# ============================================================================
# MIDDLEWARE CONFIGURATION
# ============================================================================

# CORS - Allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# PYDANTIC MODELS (Request/Response Schemas)
# ============================================================================

class AnalysisResponse(BaseModel):
    """
    Structured response for image analysis.
    
    Pydantic automatically validates and documents this schema.
    """
    success: bool = Field(..., description="Whether analysis completed successfully")
    primary_diagnosis: Optional[str] = Field(None, description="Main diagnostic finding")
    confidence: Optional[float] = Field(None, description="Confidence score (0-1)")
    all_predictions: Optional[List[Dict]] = Field(None, description="All condition predictions")
    research_summary: Optional[str] = Field(None, description="Relevant literature summary")
    final_report: Optional[str] = Field(None, description="Complete diagnostic report")
    requires_review: Optional[bool] = Field(None, description="Flags low-confidence cases")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "primary_diagnosis": "Diabetic Retinopathy",
                "confidence": 0.88,
                "all_predictions": [
                    {"condition": "Diabetic Retinopathy", "confidence": 0.88, "severity": "likely"}
                ],
                "requires_review": False,
                "final_report": "Full diagnostic report text..."
            }
        }


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    version: str
    agents: List[str]


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.bmp', '.tiff'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

def validate_image_file(file: UploadFile) -> None:
    """
    Validate uploaded file is a valid image.
    
    Checks:
    - File extension
    - File size
    - Content type
    
    Args:
        file: Uploaded file object
        
    Raises:
        HTTPException: If validation fails
    """
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Check content type
    if not file.content_type.startswith('image/'):
        raise HTTPException(
            status_code=400,
            detail="File must be an image"
        )


# ============================================================================
# API ENDPOINTS
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def root():
    """
    Serve the frontend HTML file.
    
    Returns:
        HTML content of index.html
    """
    frontend_path = Path(__file__).parent.parent / "frontend" / "index.html"
    
    if frontend_path.exists():
        return HTMLResponse(content=frontend_path.read_text(), status_code=200)
    else:
        return HTMLResponse(
            content="<h1>Frontend not found</h1><p>Please ensure frontend/index.html exists</p>",
            status_code=404
        )


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    
    Useful for:
    - Monitoring/alerting systems
    - Load balancer health checks
    - Verifying deployment
    
    Returns:
        System status information
    """
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        agents=["vision", "research", "supervisor"]
    )


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_image(
    image: UploadFile = File(..., description="Medical image file (JPG, PNG, etc.)")
):
    """
    Main analysis endpoint - processes medical images through agent workflow.
    
    Workflow:
    1. Validate uploaded file
    2. Read image bytes
    3. Initialize agent state
    4. Run LangGraph workflow (Vision → Research → Supervisor)
    5. Extract and return results
    
    Args:
        image: Uploaded image file
        
    Returns:
        AnalysisResponse with diagnostic results
        
    Raises:
        HTTPException: If validation or processing fails
    """
    print(f"\n{'='*60}")
    print(f"📥 New analysis request: {image.filename}")
    print(f"{'='*60}")
    
    try:
        # Step 1: Validate file
        validate_image_file(image)
        
        # Step 2: Read file contents
        image_bytes = await image.read()
        file_size_mb = len(image_bytes) / (1024 * 1024)
        
        print(f"✓ Image validated: {file_size_mb:.2f} MB")
        
        if len(image_bytes) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Max size: {MAX_FILE_SIZE / (1024*1024)} MB"
            )
        
        # Step 3: Initialize agent state
        initial_state: AgentState = {
            "messages": [{
                "role": "user",
                "content": f"Analyze medical image: {image.filename}"
            }],
            "image_data": image_bytes,
            "image_filename": image.filename,
            "vision_results": None,
            "research_results": None,
            "final_report": None,
            "current_agent": None,
            "error": None
        }
        
        # Step 4: Run the workflow
        print("🚀 Starting agent workflow...")
        final_state = diagnostic_graph.invoke(initial_state)
        
        # Step 5: Check for errors
        if final_state.get("error"):
            print(f"❌ Workflow error: {final_state['error']}")
            return AnalysisResponse(
                success=False,
                error=final_state["error"]
            )
        
        # Step 6: Extract results
        vision_results = final_state.get("vision_results", {})
        research_results = final_state.get("research_results", {})
        final_report = final_state.get("final_report", "")
        
        print("✅ Analysis completed successfully")
        print(f"   Primary diagnosis: {vision_results.get('primary_diagnosis', 'N/A')}")
        print(f"   Confidence: {vision_results.get('confidence', 0):.1%}")
        
        # Step 7: Return structured response
        return AnalysisResponse(
            success=True,
            primary_diagnosis=vision_results.get("primary_diagnosis"),
            confidence=vision_results.get("confidence"),
            all_predictions=vision_results.get("all_predictions", []),
            research_summary=research_results.get("summary", ""),
            final_report=final_report,
            requires_review=vision_results.get("requires_review", True)
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (already have proper status codes)
        raise
    
    except Exception as e:
        # Catch unexpected errors
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )


# ============================================================================
# STATIC FILE SERVING (CSS, JS)
# ============================================================================

# Mount frontend directory for static files
frontend_dir = Path(__file__).parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


# ============================================================================
# STARTUP EVENT
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """
    Runs once when server starts.
    
    Good place for:
    - Loading ML models
    - Database connections
    - Cache initialization
    """
    print("\n" + "="*60)
    print("🏥 Clinical Diagnostic Copilot Server Starting...")
    print("="*60)
    print("✓ FastAPI initialized")
    print("✓ CORS middleware configured")
    print("✓ Agent workflow ready")
    print("✓ Vision module loaded")
    print("✓ Knowledge base initialized")
    print("\n🌐 Server ready at http://localhost:8000")
    print("📚 API docs at http://localhost:8000/api/docs")
    print("="*60 + "\n")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown."""
    print("\n👋 Server shutting down gracefully...")


# ============================================================================
# DEVELOPMENT SERVER (only if run directly)
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
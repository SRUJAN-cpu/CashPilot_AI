"""
FastAPI Server - Main Entry Point
Provides REST API for interacting with Masumi AI Agents
"""

import os
import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

from .routes import health, agents, portfolio, mip003
# Using simplified agents that work with current LangChain
from agents.simple_agents import initialize_agents, get_agent

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifecycle manager for FastAPI app
    Initializes and cleans up agents
    """
    operational_mode = os.getenv("OPERATIONAL_MODE", "simulation")
    logger.info("=" * 70)
    logger.info("Starting CashPilot AI Agent System...")
    logger.info(f"Operational Mode: {operational_mode.upper()}")
    logger.info(f"MIP-003 Compliant: YES")
    logger.info("=" * 70)

    if operational_mode == "simulation":
        logger.info("SIMULATION MODE: Payments will be auto-approved for testing")
        logger.info("To use real Masumi payments, set OPERATIONAL_MODE=production")

    try:
        # Initialize agents with Groq API
        groq_api_key = os.getenv("GROQ_API_KEY")

        if groq_api_key and operational_mode != "api":
            logger.info("Initializing AI agents with Groq...")
            try:
                # Initialize agents and store in app.state (shared across processes)
                market_agent, strategy_agent, risk_agent = initialize_agents(groq_api_key)

                # Store in app.state so they're accessible in request handlers
                app.state.market_agent = market_agent
                app.state.strategy_agent = strategy_agent
                app.state.risk_agent = risk_agent

                logger.info("✓ Market Intelligence Agent initialized")
                logger.info("✓ Strategy Executor Agent initialized")
                logger.info("✓ Risk Guardian Agent initialized")
            except Exception as e:
                logger.error(f"Failed to initialize agents: {e}")
                logger.warning("Agents will not be available")
                app.state.market_agent = None
                app.state.strategy_agent = None
                app.state.risk_agent = None
        else:
            logger.warning("Agents not initialized (missing GROQ_API_KEY or API mode)")
            app.state.market_agent = None
            app.state.strategy_agent = None
            app.state.risk_agent = None

        yield

    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise

    finally:
        # Cleanup
        logger.info("Server shutdown complete")


# Create FastAPI app
app = FastAPI(
    title="CashPilot AI - Masumi DeFi Agents",
    description="Multi-agent DeFi portfolio optimization on Cardano via Masumi Network",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(agents.router, prefix="/agents", tags=["Agents"])
app.include_router(portfolio.router, prefix="/portfolio", tags=["Portfolio"])

# MIP-003 Standard Endpoints (Masumi Network compliance)
app.include_router(mip003.router, tags=["MIP-003 Standard"])

# Get the project root directory (one level up from api/)
BASE_DIR = Path(__file__).resolve().parent.parent

# Serve the dashboard
@app.get("/dashboard")
async def dashboard():
    """Serve the interactive dashboard"""
    dashboard_path = BASE_DIR / "dashboard.html"
    if dashboard_path.exists():
        return FileResponse(dashboard_path)
    raise HTTPException(status_code=404, detail="Dashboard not found")


@app.get("/")
async def root():
    """Root endpoint with service information"""
    operational_mode = os.getenv("OPERATIONAL_MODE", "simulation")

    return {
        "service": "CashPilot AI - Masumi DeFi Agents",
        "version": "1.0.0",
        "status": "operational",
        "operational_mode": operational_mode,
        "mip003_compliant": True,
        "agents": {
            "market_intelligence": {
                "service_url": "http://localhost:8001",
                "price_ada": 0.01
            },
            "strategy_executor": {
                "service_url": "http://localhost:8002",
                "price_ada": 0.05
            },
            "risk_guardian": {
                "service_url": "http://localhost:8003",
                "price_ada": 0.02
            }
        },
        "endpoints": {
            "documentation": "/docs",
            "health": "/health",
            "mip003": {
                "availability": "/availability",
                "input_schema": "/input_schema?agent_type=market|strategy|risk",
                "start_job": "/start_job",
                "job_status": "/status?job_id=xxx",
                "provide_input": "/provide_input"
            }
        },
        "references": {
            "masumi_docs": "https://docs.masumi.network",
            "github": "https://github.com/yourusername/CashPilot_AI"
        }
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("API_PORT", "8000"))
    host = os.getenv("API_HOST", "0.0.0.0")
    workers = int(os.getenv("API_WORKERS", "1"))

    logger.info(f"Starting server on {host}:{port}")

    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        workers=workers,
        reload=os.getenv("DEBUG", "False").lower() == "true"
    )

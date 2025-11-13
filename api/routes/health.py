"""
Health Check Routes
"""

from fastapi import APIRouter, Request
from datetime import datetime

router = APIRouter()


@router.get("/")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "CashPilot AI"
    }


@router.get("/agents")
async def agents_health(request: Request):
    """Check status of all agents"""
    try:
        market_agent = request.app.state.market_agent
        strategy_agent = request.app.state.strategy_agent
        risk_agent = request.app.state.risk_agent

        return {
            "status": "healthy",
            "agents": {
                "market_intelligence": {
                    "status": "active" if market_agent else "inactive",
                    "name": market_agent.name if market_agent else None,
                    "price_ada": market_agent.price_ada if market_agent else None
                },
                "strategy_executor": {
                    "status": "active" if strategy_agent else "inactive",
                    "name": strategy_agent.name if strategy_agent else None,
                    "price_ada": strategy_agent.price_ada if strategy_agent else None
                },
                "risk_guardian": {
                    "status": "active" if risk_agent else "inactive",
                    "name": risk_agent.name if risk_agent else None,
                    "price_ada": risk_agent.price_ada if risk_agent else None
                }
            },
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

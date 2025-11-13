"""
Portfolio Management Routes
End-to-end portfolio optimization workflows
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime

router = APIRouter()


class PortfolioOptimizationRequest(BaseModel):
    """Complete portfolio optimization request"""
    user_address: str
    current_portfolio: Dict[str, Any]
    risk_tolerance: str  # conservative, moderate, aggressive
    target_return: float
    user_wallet_id: str


class PortfolioMonitorRequest(BaseModel):
    """Portfolio monitoring request"""
    user_address: str
    portfolio: Dict[str, Any]


@router.post("/optimize")
async def optimize_portfolio(
    request: Request,
    optimization_request: PortfolioOptimizationRequest
):
    """
    Complete portfolio optimization workflow

    Steps:
    1. Market Intelligence Agent analyzes current market opportunities
    2. Strategy Executor Agent generates optimal allocation strategy
    3. Risk Guardian Agent validates the strategy
    4. Return approved strategy with transaction plan

    Total cost: 0.05 ADA (paid to Strategy Agent, which distributes to other agents)
    """
    try:
        start_time = datetime.now()

        strategy_agent = request.app.state.strategy_agent

        if not strategy_agent:
            raise HTTPException(status_code=503, detail="Strategy agent not available")

        # Generate and validate strategy (includes agent-to-agent payments)
        result = await strategy_agent.generate_strategy(
            user_portfolio=optimization_request.current_portfolio,
            risk_tolerance=optimization_request.risk_tolerance,
            target_return=optimization_request.target_return,
            requester_wallet_id=optimization_request.user_wallet_id
        )

        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()

        return {
            "success": True,
            "strategy": result["strategy"],
            "risk_validation": result["risk_validation"],
            "total_cost_ada": 0.05,
            "agent_payments": {
                "strategy_executor": 0.05,
                "market_intelligence": 0.01,
                "risk_guardian": 0.02
            },
            "processing_time_seconds": total_time,
            "timestamp": end_time.isoformat(),
            "payment_id": result.get("payment_id"),
            "next_steps": [
                "Review the recommended allocations",
                "Execute rebalancing transactions via /portfolio/execute",
                "Monitor portfolio health via /portfolio/monitor"
            ]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/monitor")
async def monitor_portfolio(
    request: Request,
    monitor_request: PortfolioMonitorRequest
):
    """
    Monitor portfolio health and risk

    Price: Free (demonstration feature)
    """
    try:
        risk_agent = request.app.state.risk_agent

        if not risk_agent:
            raise HTTPException(status_code=503, detail="Risk agent not available")

        health_report = await risk_agent.monitor_portfolio(
            portfolio=monitor_request.portfolio,
            user_address=monitor_request.user_address
        )

        return health_report

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/execute")
async def execute_strategy(
    request: Request,
    strategy_id: str,
    user_address: str
):
    """
    Execute approved portfolio strategy

    Note: In production, this would build and submit actual Cardano transactions
    """
    try:
        strategy_agent = request.app.state.strategy_agent

        if not strategy_agent:
            raise HTTPException(status_code=503, detail="Strategy agent not available")

        result = await strategy_agent.execute_strategy(
            strategy_id=strategy_id,
            user_address=user_address
        )

        return {
            "success": True,
            "execution_result": result,
            "note": "In production, actual Cardano transactions would be submitted to the blockchain"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/analytics")
async def get_portfolio_analytics(
    request: Request,
    user_address: str
):
    """
    Get portfolio analytics and insights

    Demonstrates multi-agent collaboration:
    - Market data from Market Intelligence Agent
    - Risk metrics from Risk Guardian Agent
    """
    try:
        market_agent = request.app.state.market_agent
        risk_agent = request.app.state.risk_agent

        if not market_agent or not risk_agent:
            raise HTTPException(status_code=503, detail="Agents not available")

        # Get market overview
        market_overview = await market_agent.process_query(
            "Provide overview of current Cardano DeFi market conditions"
        )

        return {
            "user_address": user_address,
            "market_overview": market_overview,
            "timestamp": datetime.now().isoformat(),
            "recommendation": "Use /portfolio/optimize to generate personalized strategy"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

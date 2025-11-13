"""
Agent Interaction Routes
Endpoints for interacting with individual agents
"""

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from typing import Optional, Dict, Any

router = APIRouter()


class MarketQueryRequest(BaseModel):
    """Market data query request"""
    query: str
    requester_wallet_id: Optional[str] = None


class StrategyRequest(BaseModel):
    """Strategy generation request"""
    user_portfolio: Dict[str, Any]
    risk_tolerance: str  # conservative, moderate, aggressive
    target_return: float
    requester_wallet_id: Optional[str] = None


class RiskAssessmentRequest(BaseModel):
    """Risk assessment request"""
    strategy: Dict[str, Any]
    requester_wallet_id: Optional[str] = None


@router.post("/market/query")
async def query_market_agent(request: Request, query_request: MarketQueryRequest):
    """
    Query the Market Intelligence Agent for DeFi market data

    Price: 0.01 ADA per query
    """
    try:
        market_agent = request.app.state.market_agent

        if not market_agent:
            raise HTTPException(status_code=503, detail="Market agent not available")

        result = await market_agent.process_query(
            query=query_request.query,
            requester_wallet_id=query_request.requester_wallet_id
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/market/opportunities")
async def get_yield_opportunities(
    request: Request,
    min_tvl: float = 100_000,
    min_apr: float = 5.0
):
    """
    Get best yield opportunities across Cardano DeFi protocols

    Price: 0.01 ADA
    """
    try:
        market_agent = request.app.state.market_agent

        if not market_agent:
            raise HTTPException(status_code=503, detail="Market agent not available")

        result = await market_agent.get_yield_opportunities(
            min_tvl=min_tvl,
            min_apr=min_apr
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/strategy/generate")
async def generate_strategy(request: Request, strategy_request: StrategyRequest):
    """
    Generate optimized portfolio strategy

    Price: 0.05 ADA per execution
    Note: Strategy Agent will pay 0.01 ADA to Market Agent and 0.02 ADA to Risk Agent
    """
    try:
        strategy_agent = request.app.state.strategy_agent

        if not strategy_agent:
            raise HTTPException(status_code=503, detail="Strategy agent not available")

        result = await strategy_agent.generate_strategy(
            user_portfolio=strategy_request.user_portfolio,
            risk_tolerance=strategy_request.risk_tolerance,
            target_return=strategy_request.target_return,
            requester_wallet_id=strategy_request.requester_wallet_id
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/risk/assess")
async def assess_risk(request: Request, assessment_request: RiskAssessmentRequest):
    """
    Assess risk of a portfolio strategy

    Price: 0.02 ADA per assessment
    """
    try:
        risk_agent = request.app.state.risk_agent

        if not risk_agent:
            raise HTTPException(status_code=503, detail="Risk agent not available")

        result = await risk_agent.assess_strategy(
            strategy=assessment_request.strategy,
            requester_wallet_id=assessment_request.requester_wallet_id
        )

        return result

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/info")
async def get_agents_info(request: Request):
    """Get information about all registered agents"""
    try:
        market_agent = request.app.state.market_agent
        strategy_agent = request.app.state.strategy_agent
        risk_agent = request.app.state.risk_agent

        return {
            "agents": {
                "market_intelligence": {
                    "name": "Market Intelligence Agent",
                    "agent_id": market_agent.agent_id if market_agent else None,
                    "capabilities": ["market_data", "yield_analysis", "protocol_comparison"],
                    "price_per_request": market_agent.price_per_query if market_agent else 0.01,
                    "wallet_id": market_agent.wallet_id if market_agent else None
                },
                "strategy_executor": {
                    "name": "Strategy Executor Agent",
                    "agent_id": strategy_agent.agent_id if strategy_agent else None,
                    "capabilities": ["portfolio_optimization", "strategy_generation", "transaction_execution"],
                    "price_per_request": strategy_agent.price_per_execution if strategy_agent else 0.05,
                    "wallet_id": strategy_agent.wallet_id if strategy_agent else None,
                    "collaborates_with": ["market_intelligence", "risk_guardian"]
                },
                "risk_guardian": {
                    "name": "Risk Guardian Agent",
                    "agent_id": risk_agent.agent_id if risk_agent else None,
                    "capabilities": ["risk_assessment", "strategy_validation", "portfolio_monitoring"],
                    "price_per_request": risk_agent.price_per_check if risk_agent else 0.02,
                    "wallet_id": risk_agent.wallet_id if risk_agent else None
                }
            },
            "monetization_model": {
                "market_intelligence": "0.01 ADA per query",
                "strategy_executor": "0.05 ADA per execution (pays 0.03 ADA to other agents)",
                "risk_guardian": "0.02 ADA per assessment"
            }
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

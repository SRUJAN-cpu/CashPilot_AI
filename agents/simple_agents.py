"""
Simplified AI Agents for CashPilot Demo
Uses direct Groq API calls without complex LangChain dependencies
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class SimpleMarketAgent:
    """Market Intelligence Agent - Simplified for demo"""

    def __init__(self, groq_api_key: str):
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=groq_api_key,
            temperature=0.3
        )
        self.price_ada = 0.01
        self.name = "Market Intelligence Agent"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute market analysis"""
        logger.info(f"Market Agent executing with input: {input_data}")

        query = input_data.get("query", "Analyze Cardano DeFi opportunities")
        min_apr = input_data.get("min_apr", 5.0)

        system_prompt = f"""You are the Market Intelligence Agent for Cardano DeFi.
Provide real-time analysis of DeFi opportunities on Cardano blockchain.

Focus on protocols like Minswap, SundaeSwap, Liqwid, Indigo, etc.
Current date: {datetime.now().strftime('%Y-%m-%d')}

Respond with:
1. Top 3 yield opportunities
2. Current APRs
3. TVL metrics
4. Risk assessment

Format as structured JSON."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Query: {query}\nMinimum APR filter: {min_apr}%")
        ]

        try:
            response = self.llm.invoke(messages)

            return {
                "success": True,
                "agent": "market_intelligence",
                "query": query,
                "analysis": response.content,
                "opportunities": [
                    {
                        "protocol": "Minswap",
                        "pool": "ADA/DJED",
                        "apr": 12.5,
                        "tvl_ada": 2500000,
                        "risk_score": 25
                    },
                    {
                        "protocol": "SundaeSwap",
                        "pool": "ADA/MIN",
                        "apr": 15.8,
                        "tvl_ada": 1800000,
                        "risk_score": 35
                    },
                    {
                        "protocol": "Liqwid",
                        "asset": "ADA Lending",
                        "apr": 8.2,
                        "tvl_ada": 5000000,
                        "risk_score": 15
                    }
                ],
                "summary": response.content[:500],
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Market Agent error: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": "market_intelligence"
            }


class SimpleStrategyAgent:
    """Strategy Executor Agent - Simplified for demo"""

    def __init__(self, groq_api_key: str):
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=groq_api_key,
            temperature=0.3
        )
        self.price_ada = 0.05
        self.name = "Strategy Executor Agent"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate portfolio strategy"""
        logger.info(f"Strategy Agent executing with input: {input_data}")

        portfolio = input_data.get("user_portfolio", {})
        risk_tolerance = input_data.get("risk_tolerance", "moderate")
        target_return = input_data.get("target_return", 12.0)

        system_prompt = f"""You are the Strategy Executor Agent for DeFi portfolio optimization.
Analyze portfolios and generate optimal allocation strategies for Cardano DeFi.

Consider:
- Risk tolerance: {risk_tolerance}
- Target return: {target_return}%
- Current portfolio value: {portfolio.get('ada_balance', 0)} ADA

Provide a detailed allocation strategy across multiple protocols."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Generate optimal portfolio strategy for: {portfolio}")
        ]

        try:
            response = self.llm.invoke(messages)

            return {
                "success": True,
                "agent": "strategy_executor",
                "strategy_id": f"strat-{datetime.now().timestamp()}",
                "recommended_allocations": [
                    {
                        "protocol": "Minswap",
                        "pool": "ADA/DJED",
                        "allocation_percent": 40,
                        "expected_apr": 12.5,
                        "risk_score": 25
                    },
                    {
                        "protocol": "SundaeSwap",
                        "pool": "ADA/MIN",
                        "allocation_percent": 30,
                        "expected_apr": 15.8,
                        "risk_score": 35
                    },
                    {
                        "protocol": "Liqwid",
                        "asset": "ADA",
                        "allocation_percent": 30,
                        "expected_apr": 8.2,
                        "risk_score": 20
                    }
                ],
                "expected_portfolio_apr": 12.5,
                "expected_portfolio_risk": 27.5,
                "ai_reasoning": response.content,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Strategy Agent error: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": "strategy_executor"
            }


class SimpleRiskAgent:
    """Risk Guardian Agent - Simplified for demo"""

    def __init__(self, groq_api_key: str):
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=groq_api_key,
            temperature=0.1
        )
        self.price_ada = 0.02
        self.name = "Risk Guardian Agent"

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess portfolio risk"""
        logger.info(f"Risk Agent executing with input: {input_data}")

        strategy = input_data.get("strategy", {})

        system_prompt = """You are the Risk Guardian Agent for DeFi portfolio analysis.
Evaluate portfolio strategies and provide comprehensive risk assessments.

Analyze:
- Smart contract risk
- Liquidity risk
- Concentration risk
- Market volatility
- Protocol safety scores

Provide risk scores (0-100) and recommendations."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Assess risk for strategy: {strategy}")
        ]

        try:
            response = self.llm.invoke(messages)

            return {
                "success": True,
                "agent": "risk_guardian",
                "approved": True,
                "overall_risk_score": 27.5,
                "risk_breakdown": {
                    "smart_contract_risk": 20,
                    "liquidity_risk": 25,
                    "concentration_risk": 30,
                    "market_volatility": 35
                },
                "warnings": [
                    "Moderate concentration in volatile assets",
                    "Consider diversifying across more protocols"
                ],
                "recommendations": [
                    "Limit single-protocol exposure to <40%",
                    "Monitor liquidity levels daily",
                    "Set stop-loss at -15%"
                ],
                "ai_analysis": response.content,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Risk Agent error: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent": "risk_guardian"
            }


# Global agent instances
market_agent: Optional[SimpleMarketAgent] = None
strategy_agent: Optional[SimpleStrategyAgent] = None
risk_agent: Optional[SimpleRiskAgent] = None


def initialize_agents(groq_api_key: str):
    """Initialize all agents"""
    global market_agent, strategy_agent, risk_agent

    logger.info("Initializing simplified agents with Groq...")

    market_agent = SimpleMarketAgent(groq_api_key)
    strategy_agent = SimpleStrategyAgent(groq_api_key)
    risk_agent = SimpleRiskAgent(groq_api_key)

    logger.info("✓ All agents initialized successfully!")

    return market_agent, strategy_agent, risk_agent


def get_agent(agent_type: str):
    """Get agent by type"""
    agents = {
        "market": market_agent,
        "strategy": strategy_agent,
        "risk": risk_agent
    }
    return agents.get(agent_type)

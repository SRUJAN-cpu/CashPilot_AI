"""
Strategy Executor Agent
Generates optimal portfolio rebalancing strategies
Monetized via Masumi Network at $0.05/execution
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
try:
    from langchain.agents import AgentExecutor, create_openai_functions_agent
except ImportError:
    from langchain_core.agents import AgentExecutor
    from langchain.agents import create_react_agent as create_openai_functions_agent
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory

from .optimizer import PortfolioOptimizer
from ...masumi_integration import PaymentService, RegistryService
from ...masumi_integration.registry_service import AgentCapability

logger = logging.getLogger(__name__)


class StrategyExecutorAgent:
    """
    Strategy Executor Agent - Generates and executes DeFi portfolio strategies

    Capabilities:
    - Portfolio optimization algorithms
    - Risk-adjusted yield maximization
    - Automated rebalancing strategies
    - Multi-protocol portfolio allocation

    Monetization: $0.05 per strategy execution
    Pays Market Intelligence Agent for data ($0.01/query)
    Pays Risk Guardian Agent for validation ($0.02/check)
    """

    def __init__(
        self,
        groq_api_key: str,
        wallet_id: str,
        wallet_address: str,
        market_agent_wallet_id: str,
        risk_agent_wallet_id: str,
        service_url: str = "http://localhost:8002",
        price_per_execution: float = 0.05
    ):
        self.wallet_id = wallet_id
        self.wallet_address = wallet_address
        self.market_agent_wallet_id = market_agent_wallet_id
        self.risk_agent_wallet_id = risk_agent_wallet_id
        self.service_url = service_url
        self.price_per_execution = price_per_execution
        self.agent_id: Optional[str] = None

        # Initialize Groq LLM (FREE and fast!)
        self.llm = ChatGroq(
            model="llama-3.1-70b-versatile",
            api_key=groq_api_key,
            temperature=0.3
        )

        # Initialize optimizer
        self.optimizer = PortfolioOptimizer()

        # Create agent prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the Strategy Executor Agent, a specialized portfolio
optimization AI running on the Masumi Network.

Your role is to:
1. Analyze user portfolios and investment goals
2. Request market data from the Market Intelligence Agent
3. Generate optimal portfolio allocation strategies
4. Submit strategies to Risk Guardian Agent for validation
5. Execute approved rebalancing transactions

You focus on maximizing risk-adjusted returns while considering:
- User risk tolerance
- Capital efficiency
- Protocol safety and TVL
- Gas fees and transaction costs
- Diversification across protocols

Always explain your reasoning and provide clear allocation recommendations.

Current timestamp: {timestamp}
"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Masumi services
        self.payment_service = PaymentService()
        self.registry_service = RegistryService()

        logger.info("Strategy Executor Agent initialized")

    async def register_on_masumi(self) -> str:
        """Register agent on Masumi Network"""
        try:
            agent_metadata = await self.registry_service.register_agent(
                name="Strategy Executor Agent",
                description="AI-powered DeFi portfolio optimization and automated rebalancing",
                capabilities=[
                    AgentCapability.STRATEGY_GENERATION,
                    AgentCapability.PORTFOLIO_ANALYSIS,
                    AgentCapability.TRANSACTION_EXECUTION
                ],
                service_url=self.service_url,
                wallet_id=self.wallet_id,
                wallet_address=self.wallet_address,
                price_per_request=self.price_per_execution,
                metadata={
                    "version": "1.0.0",
                    "collaborates_with": ["market_intelligence", "risk_guardian"],
                    "optimization_algorithms": ["mean_variance", "risk_parity", "max_sharpe"],
                    "supported_protocols": ["minswap", "sundaeswap", "liqwid"]
                }
            )

            self.agent_id = agent_metadata.agent_id
            logger.info(f"Agent registered on Masumi: {self.agent_id}")
            return self.agent_id

        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
            raise

    async def _request_market_data(
        self,
        market_agent_url: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Request market data from Market Intelligence Agent
        Pays for the service via Masumi

        Args:
            market_agent_url: Market agent service URL
            query: Data query

        Returns:
            Market data response
        """
        try:
            # Pay Market Intelligence Agent
            payment = await self.payment_service.create_payment(
                from_wallet_id=self.wallet_id,
                to_wallet_id=self.market_agent_wallet_id,
                amount_ada=0.01,  # Market agent price
                description=f"Market data request: {query[:50]}",
                metadata={
                    "from_agent": "strategy_executor",
                    "to_agent": "market_intelligence",
                    "query": query
                }
            )

            logger.info(
                f"Paid Market Intelligence Agent: 0.01 ADA "
                f"(Payment: {payment.payment_id})"
            )

            # Make request to market agent
            # In production, this would be an HTTP request to market_agent_url
            # For now, we'll simulate the response
            market_data = {
                "query": query,
                "response": "Market data retrieved successfully",
                "payment_id": payment.payment_id
            }

            return market_data

        except Exception as e:
            logger.error(f"Failed to request market data: {e}")
            raise

    async def _request_risk_validation(
        self,
        risk_agent_url: str,
        strategy: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Request risk validation from Risk Guardian Agent
        Pays for the service via Masumi

        Args:
            risk_agent_url: Risk agent service URL
            strategy: Strategy to validate

        Returns:
            Risk validation response
        """
        try:
            # Pay Risk Guardian Agent
            payment = await self.payment_service.create_payment(
                from_wallet_id=self.wallet_id,
                to_wallet_id=self.risk_agent_wallet_id,
                amount_ada=0.02,  # Risk agent price
                description="Strategy risk validation",
                metadata={
                    "from_agent": "strategy_executor",
                    "to_agent": "risk_guardian",
                    "strategy_id": strategy.get("strategy_id", "unknown")
                }
            )

            logger.info(
                f"Paid Risk Guardian Agent: 0.02 ADA "
                f"(Payment: {payment.payment_id})"
            )

            # In production: HTTP request to risk_agent_url
            risk_validation = {
                "strategy_id": strategy.get("strategy_id"),
                "approved": True,
                "risk_score": 35.0,
                "warnings": [],
                "payment_id": payment.payment_id
            }

            return risk_validation

        except Exception as e:
            logger.error(f"Failed to request risk validation: {e}")
            raise

    async def generate_strategy(
        self,
        user_portfolio: Dict[str, Any],
        risk_tolerance: str,
        target_return: float,
        requester_wallet_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate optimal portfolio strategy

        Args:
            user_portfolio: Current portfolio holdings
            risk_tolerance: Risk level (conservative, moderate, aggressive)
            target_return: Target APR
            requester_wallet_id: User's wallet for payment

        Returns:
            Strategy with allocations and transactions
        """
        try:
            start_time = datetime.now()

            # Step 1: Request market data
            logger.info("Requesting market data from Market Intelligence Agent...")
            market_data = await self._request_market_data(
                "http://localhost:8001",  # Market agent URL
                f"Get yield opportunities for {risk_tolerance} risk profile"
            )

            # Step 2: Generate strategy using optimizer
            logger.info("Generating portfolio strategy...")
            strategy = self.optimizer.optimize_portfolio(
                current_portfolio=user_portfolio,
                risk_tolerance=risk_tolerance,
                target_return=target_return
            )

            # Step 3: Request risk validation
            logger.info("Requesting risk validation from Risk Guardian Agent...")
            risk_validation = await self._request_risk_validation(
                "http://localhost:8003",  # Risk agent URL
                strategy
            )

            # Step 4: Finalize strategy
            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            response = {
                "agent": "strategy_executor",
                "agent_id": self.agent_id,
                "strategy": strategy,
                "risk_validation": risk_validation,
                "market_data_source": "market_intelligence",
                "timestamp": end_time.isoformat(),
                "processing_time_seconds": processing_time,
                "price_ada": self.price_per_execution,
                "costs": {
                    "market_data": 0.01,
                    "risk_validation": 0.02,
                    "total": 0.03
                },
                "net_revenue_ada": self.price_per_execution - 0.03
            }

            # Create payment from requester
            if requester_wallet_id:
                payment = await self.payment_service.create_payment(
                    from_wallet_id=requester_wallet_id,
                    to_wallet_id=self.wallet_id,
                    amount_ada=self.price_per_execution,
                    description="Portfolio strategy generation",
                    metadata={
                        "agent": "strategy_executor",
                        "strategy_id": strategy["strategy_id"],
                        "timestamp": end_time.isoformat()
                    }
                )

                response["payment_id"] = payment.payment_id
                response["payment_status"] = payment.status.value

            logger.info(f"Strategy generated successfully in {processing_time:.2f}s")
            return response

        except Exception as e:
            logger.error(f"Failed to generate strategy: {e}")
            raise

    async def execute_strategy(
        self,
        strategy_id: str,
        user_address: str
    ) -> Dict[str, Any]:
        """
        Execute approved strategy transactions

        Args:
            strategy_id: Strategy to execute
            user_address: User's Cardano address

        Returns:
            Execution results with transaction hashes
        """
        try:
            # In production: build and submit actual transactions
            logger.info(f"Executing strategy {strategy_id} for {user_address}")

            execution_result = {
                "strategy_id": strategy_id,
                "status": "executed",
                "transactions": [
                    {
                        "type": "swap",
                        "protocol": "minswap",
                        "from": "ADA",
                        "to": "DJED",
                        "amount": 1000,
                        "tx_hash": "mock_tx_hash_1"
                    }
                ],
                "timestamp": datetime.now().isoformat()
            }

            logger.info(f"Strategy {strategy_id} executed successfully")
            return execution_result

        except Exception as e:
            logger.error(f"Failed to execute strategy: {e}")
            raise

    async def close(self):
        """Cleanup resources"""
        await self.payment_service.close()
        await self.registry_service.close()

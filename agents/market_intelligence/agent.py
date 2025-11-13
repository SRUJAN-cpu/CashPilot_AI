"""
Market Intelligence Agent
Provides real-time DeFi market data and analysis
Monetized via Masumi Network at $0.01/query
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime
try:
    from langchain.agents import AgentExecutor, create_openai_functions_agent
except ImportError:
    from langchain_core.agents import AgentExecutor
    from langchain.agents import create_react_agent as create_openai_functions_agent
from langchain_groq import ChatGroq
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory

from .tools import MarketDataTools
from ...masumi_integration import PaymentService, RegistryService, WalletManager
from ...masumi_integration.registry_service import AgentCapability, AgentStatus

logger = logging.getLogger(__name__)


class MarketIntelligenceAgent:
    """
    Market Intelligence Agent - Provides DeFi market data and analysis

    Capabilities:
    - Real-time yield rates from Cardano DEXs (Minswap, SundaeSwap)
    - TVL and liquidity metrics
    - Protocol comparison and ranking
    - Yield opportunity identification

    Monetization: $0.01 per query via Masumi payments
    """

    def __init__(
        self,
        groq_api_key: str,
        wallet_id: str,
        wallet_address: str,
        service_url: str = "http://localhost:8001",
        price_per_query: float = 0.01
    ):
        self.wallet_id = wallet_id
        self.wallet_address = wallet_address
        self.service_url = service_url
        self.price_per_query = price_per_query
        self.agent_id: Optional[str] = None

        # Initialize Groq LLM (FREE and fast!)
        self.llm = ChatGroq(
            model="llama-3.1-70b-versatile",  # Free tier model
            api_key=groq_api_key,
            temperature=0.1
        )

        # Initialize tools
        self.tools = MarketDataTools()
        self.langchain_tools = self.tools.get_langchain_tools()

        # Create agent prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the Market Intelligence Agent, a specialized AI agent
running on the Masumi Network providing real-time DeFi market data and analysis for Cardano.

Your capabilities include:
- Fetching yield rates from Minswap, SundaeSwap, and other Cardano DEXs
- Analyzing liquidity pool metrics (TVL, volume, fees)
- Comparing protocols and identifying best yield opportunities
- Providing risk-adjusted return analysis

Always provide accurate, data-driven insights based on real blockchain data.
Format your responses clearly with specific numbers and recommendations.

Current timestamp: {timestamp}
"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Create agent
        self.agent = create_openai_functions_agent(
            llm=self.llm,
            tools=self.langchain_tools,
            prompt=self.prompt
        )

        # Create executor
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )

        self.executor = AgentExecutor(
            agent=self.agent,
            tools=self.langchain_tools,
            memory=self.memory,
            verbose=True,
            max_iterations=5
        )

        # Masumi services
        self.payment_service = PaymentService()
        self.registry_service = RegistryService()

        logger.info("Market Intelligence Agent initialized")

    async def register_on_masumi(self) -> str:
        """
        Register agent on Masumi Network registry

        Returns:
            Agent ID from Masumi registry
        """
        try:
            agent_metadata = await self.registry_service.register_agent(
                name="Market Intelligence Agent",
                description="Real-time DeFi market data and yield analysis for Cardano protocols",
                capabilities=[
                    AgentCapability.MARKET_DATA,
                    AgentCapability.PORTFOLIO_ANALYSIS
                ],
                service_url=self.service_url,
                wallet_id=self.wallet_id,
                wallet_address=self.wallet_address,
                price_per_request=self.price_per_query,
                metadata={
                    "version": "1.0.0",
                    "supported_protocols": ["minswap", "sundaeswap", "liqwid"],
                    "data_sources": ["blockfrost", "protocol_apis"],
                    "update_frequency": "real-time"
                }
            )

            self.agent_id = agent_metadata.agent_id
            logger.info(f"Agent registered on Masumi: {self.agent_id}")
            return self.agent_id

        except Exception as e:
            logger.error(f"Failed to register agent on Masumi: {e}")
            raise

    async def process_query(
        self,
        query: str,
        requester_wallet_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a market data query

        Args:
            query: Market data query
            requester_wallet_id: Wallet ID of requesting agent/user for payment

        Returns:
            Query response with market data
        """
        try:
            start_time = datetime.now()

            # Execute query using LangChain agent
            result = await self.executor.ainvoke({
                "input": query,
                "timestamp": start_time.isoformat()
            })

            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            response = {
                "agent": "market_intelligence",
                "agent_id": self.agent_id,
                "query": query,
                "response": result["output"],
                "timestamp": end_time.isoformat(),
                "processing_time_seconds": processing_time,
                "price_ada": self.price_per_query,
                "requester_wallet": requester_wallet_id,
                "payment_required": requester_wallet_id is not None
            }

            # Create payment if requester provided
            if requester_wallet_id:
                payment = await self.payment_service.create_payment(
                    from_wallet_id=requester_wallet_id,
                    to_wallet_id=self.wallet_id,
                    amount_ada=self.price_per_query,
                    description=f"Market Intelligence Query: {query[:50]}",
                    metadata={
                        "agent": "market_intelligence",
                        "query": query,
                        "timestamp": end_time.isoformat()
                    }
                )

                response["payment_id"] = payment.payment_id
                response["payment_status"] = payment.status.value

                logger.info(
                    f"Payment created: {self.price_per_query} ADA from "
                    f"{requester_wallet_id} (Payment: {payment.payment_id})"
                )

            logger.info(f"Query processed in {processing_time:.2f}s")
            return response

        except Exception as e:
            logger.error(f"Failed to process query: {e}")
            raise

    async def get_yield_opportunities(
        self,
        min_tvl: float = 100_000,
        min_apr: float = 5.0
    ) -> Dict[str, Any]:
        """
        Get best yield opportunities across protocols

        Args:
            min_tvl: Minimum TVL filter
            min_apr: Minimum APR filter

        Returns:
            List of opportunities
        """
        query = f"Find yield opportunities with min TVL {min_tvl} ADA and min APR {min_apr}%"
        return await self.process_query(query)

    async def compare_protocols(self, protocols: list[str]) -> Dict[str, Any]:
        """
        Compare DeFi protocols

        Args:
            protocols: List of protocol names

        Returns:
            Comparison data
        """
        query = f"Compare these Cardano DeFi protocols: {', '.join(protocols)}"
        return await self.process_query(query)

    async def get_pool_data(self, protocol: str, pool_id: str) -> Dict[str, Any]:
        """
        Get specific pool data

        Args:
            protocol: Protocol name
            pool_id: Pool identifier

        Returns:
            Pool metrics
        """
        query = f"Get detailed data for {protocol} pool {pool_id}"
        return await self.process_query(query)

    async def close(self):
        """Cleanup resources"""
        await self.payment_service.close()
        await self.registry_service.close()
        await self.tools.close()

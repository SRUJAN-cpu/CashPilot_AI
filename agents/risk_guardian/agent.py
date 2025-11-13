"""
Risk Guardian Agent
Validates portfolio strategies and monitors risk
Monetized via Masumi Network at $0.02/check
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

from .risk_models import RiskAnalyzer
from ...masumi_integration import PaymentService, RegistryService
from ...masumi_integration.registry_service import AgentCapability

logger = logging.getLogger(__name__)


class RiskGuardianAgent:
    """
    Risk Guardian Agent - Validates strategies and monitors portfolio risk

    Capabilities:
    - Strategy risk assessment
    - Portfolio health monitoring
    - Protocol safety validation
    - Stop-loss and safety checks

    Monetization: $0.02 per risk assessment
    """

    def __init__(
        self,
        groq_api_key: str,
        wallet_id: str,
        wallet_address: str,
        service_url: str = "http://localhost:8003",
        price_per_check: float = 0.02
    ):
        self.wallet_id = wallet_id
        self.wallet_address = wallet_address
        self.service_url = service_url
        self.price_per_check = price_per_check
        self.agent_id: Optional[str] = None

        # Initialize Groq LLM (FREE and fast!)
        self.llm = ChatGroq(
            model="llama-3.1-70b-versatile",
            api_key=groq_api_key,
            temperature=0
        )

        # Initialize risk analyzer
        self.risk_analyzer = RiskAnalyzer()

        # Create prompt
        self.prompt = ChatPromptTemplate.from_messages([
            ("system", """You are the Risk Guardian Agent, a specialized risk management
AI running on the Masumi Network.

Your responsibilities:
1. Validate portfolio strategies for risk exposure
2. Identify potential protocol risks and vulnerabilities
3. Monitor portfolio health and concentration
4. Enforce risk limits and safety checks
5. Provide risk scores and recommendations

Risk Assessment Criteria:
- Protocol safety (TVL, audit status, track record)
- Portfolio diversification
- Concentration risk
- Smart contract risk
- Liquidity risk
- Market volatility exposure

You MUST reject strategies that exceed safe risk thresholds.
Always provide clear explanations for your risk assessments.

Current timestamp: {timestamp}
"""),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Masumi services
        self.payment_service = PaymentService()
        self.registry_service = RegistryService()

        logger.info("Risk Guardian Agent initialized")

    async def register_on_masumi(self) -> str:
        """Register agent on Masumi Network"""
        try:
            agent_metadata = await self.registry_service.register_agent(
                name="Risk Guardian Agent",
                description="Portfolio risk assessment and strategy validation for DeFi safety",
                capabilities=[
                    AgentCapability.RISK_ASSESSMENT
                ],
                service_url=self.service_url,
                wallet_id=self.wallet_id,
                wallet_address=self.wallet_address,
                price_per_request=self.price_per_check,
                metadata={
                    "version": "1.0.0",
                    "risk_models": ["concentration", "protocol_safety", "liquidity"],
                    "max_risk_score": 70,
                    "assessment_criteria": [
                        "protocol_tvl",
                        "smart_contract_audits",
                        "diversification",
                        "liquidity_depth"
                    ]
                }
            )

            self.agent_id = agent_metadata.agent_id
            logger.info(f"Agent registered on Masumi: {self.agent_id}")
            return self.agent_id

        except Exception as e:
            logger.error(f"Failed to register agent: {e}")
            raise

    async def assess_strategy(
        self,
        strategy: Dict[str, Any],
        requester_wallet_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Assess risk of a portfolio strategy

        Args:
            strategy: Strategy to assess
            requester_wallet_id: Requester's wallet for payment

        Returns:
            Risk assessment with approval/rejection
        """
        try:
            start_time = datetime.now()

            # Analyze strategy risk
            risk_analysis = self.risk_analyzer.analyze_strategy(strategy)

            # Determine approval
            approved = risk_analysis["overall_risk_score"] <= 70
            if not approved:
                logger.warning(
                    f"Strategy rejected: Risk score {risk_analysis['overall_risk_score']} "
                    f"exceeds threshold of 70"
                )

            end_time = datetime.now()
            processing_time = (end_time - start_time).total_seconds()

            response = {
                "agent": "risk_guardian",
                "agent_id": self.agent_id,
                "strategy_id": strategy.get("strategy_id"),
                "approved": approved,
                "risk_analysis": risk_analysis,
                "timestamp": end_time.isoformat(),
                "processing_time_seconds": processing_time,
                "price_ada": self.price_per_check
            }

            # Create payment from requester
            if requester_wallet_id:
                payment = await self.payment_service.create_payment(
                    from_wallet_id=requester_wallet_id,
                    to_wallet_id=self.wallet_id,
                    amount_ada=self.price_per_check,
                    description=f"Risk assessment for strategy {strategy.get('strategy_id', 'unknown')[:16]}",
                    metadata={
                        "agent": "risk_guardian",
                        "strategy_id": strategy.get("strategy_id"),
                        "approved": approved,
                        "risk_score": risk_analysis["overall_risk_score"]
                    }
                )

                response["payment_id"] = payment.payment_id
                response["payment_status"] = payment.status.value

                logger.info(
                    f"Payment received: 0.02 ADA from {requester_wallet_id} "
                    f"(Payment: {payment.payment_id})"
                )

            logger.info(
                f"Risk assessment complete: {'APPROVED' if approved else 'REJECTED'} "
                f"(Risk Score: {risk_analysis['overall_risk_score']:.1f})"
            )

            return response

        except Exception as e:
            logger.error(f"Failed to assess strategy: {e}")
            raise

    async def monitor_portfolio(
        self,
        portfolio: Dict[str, Any],
        user_address: str
    ) -> Dict[str, Any]:
        """
        Monitor existing portfolio for risk issues

        Args:
            portfolio: Current portfolio holdings
            user_address: User's Cardano address

        Returns:
            Portfolio health report
        """
        try:
            health_report = self.risk_analyzer.analyze_portfolio_health(portfolio)

            alerts = []
            if health_report["concentration_risk"] > 60:
                alerts.append({
                    "severity": "high",
                    "message": "High concentration risk detected",
                    "recommendation": "Diversify holdings across more protocols"
                })

            if health_report["liquidity_risk"] > 50:
                alerts.append({
                    "severity": "medium",
                    "message": "Liquidity risk elevated",
                    "recommendation": "Consider moving to higher TVL pools"
                })

            return {
                "agent": "risk_guardian",
                "user_address": user_address,
                "health_report": health_report,
                "alerts": alerts,
                "overall_health": "healthy" if not alerts else "warning",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to monitor portfolio: {e}")
            raise

    async def validate_transaction(
        self,
        transaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a transaction before execution

        Args:
            transaction: Transaction to validate

        Returns:
            Validation result
        """
        try:
            validation = self.risk_analyzer.validate_transaction(transaction)

            return {
                "agent": "risk_guardian",
                "transaction_type": transaction.get("type"),
                "approved": validation["approved"],
                "risk_score": validation["risk_score"],
                "warnings": validation.get("warnings", []),
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to validate transaction: {e}")
            raise

    async def close(self):
        """Cleanup resources"""
        await self.payment_service.close()
        await self.registry_service.close()

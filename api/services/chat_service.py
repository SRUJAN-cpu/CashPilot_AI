"""
Chat Service
Handles message processing with NLP and agent integration
"""

import logging
import os
from typing import Dict, Any, List, Optional
from supabase import Client

from agents.nlp.conversation_handler import ConversationHandler
from agents.simple_agents import get_agent

logger = logging.getLogger(__name__)


class ChatService:
    """Service for processing chat messages with AI agents"""

    def __init__(self, groq_api_key: str):
        self.conversation_handler = ConversationHandler(groq_api_key)
        logger.info("✓ Chat service initialized")

    async def process_user_message(
        self,
        user_message: str,
        conversation_id: str,
        supabase: Client,
        app_state: Any
    ) -> str:
        """
        Process user message through NLP and appropriate agent

        Returns assistant's response text
        """
        try:
            # Get conversation history for context
            history = await self._get_conversation_history(conversation_id, supabase)

            # Process message with NLP layer
            nlp_result = await self.conversation_handler.process_message(
                user_message,
                conversation_id,
                history
            )

            logger.info(f"NLP Result - Intent: {nlp_result['intent']}, Agent: {nlp_result['agent_type']}")

            # Handle based on intent
            if nlp_result["intent"] == "clarification":
                # Return clarification question
                return nlp_result["response"]

            elif nlp_result["intent"] == "greeting":
                return await self._handle_greeting()

            elif nlp_result["intent"] == "help":
                return await self._handle_help()

            elif nlp_result.get("metadata", {}).get("requires_agent"):
                # Route to appropriate agent
                return await self._route_to_agent(nlp_result, app_state)

            else:
                return "I understand you're asking about something, but I'm not quite sure what. Could you rephrase that?"

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "I encountered an error processing your request. Please try again."

    async def _get_conversation_history(
        self,
        conversation_id: str,
        supabase: Client,
        limit: int = 10
    ) -> List[Dict]:
        """Get recent conversation history"""
        try:
            response = supabase.table("messages")\
                .select("role, content")\
                .eq("conversation_id", conversation_id)\
                .order("timestamp", desc=False)\
                .limit(limit)\
                .execute()

            return response.data if response.data else []
        except Exception as e:
            logger.error(f"Error fetching history: {e}")
            return []

    async def _handle_greeting(self) -> str:
        """Handle greeting messages"""
        return ("Hello! 👋 I'm CashPilot AI, your DeFi portfolio assistant for Cardano.\n\n"
                "I can help you with:\n"
                "• Portfolio optimization and allocation strategies\n"
                "• Current market yields and opportunities\n"
                "• Risk assessment for your portfolio\n"
                "• Portfolio management and tracking\n\n"
                "What would you like help with today?")

    async def _handle_help(self) -> str:
        """Handle help requests"""
        return ("I can help you with DeFi portfolio management on Cardano! Here are some things you can ask:\n\n"
                "📊 **Market Data:**\n"
                "• \"What are the best yields right now?\"\n"
                "• \"Show me Minswap pools\"\n"
                "• \"Compare DEX rates\"\n\n"
                "🎯 **Portfolio Optimization:**\n"
                "• \"Optimize my 10,000 ADA portfolio\"\n"
                "• \"I want moderate risk allocation\"\n"
                "• \"Target 12% APR return\"\n\n"
                "🛡️ **Risk Analysis:**\n"
                "• \"Is this allocation safe?\"\n"
                "• \"What's my portfolio risk?\"\n"
                "• \"Assess this strategy\"\n\n"
                "💼 **Portfolio Management:**\n"
                "• \"Save my portfolio\"\n"
                "• \"Show my portfolios\"\n"
                "• \"Track my investments\"\n\n"
                "Just ask naturally - I'll understand! 😊")

    async def _route_to_agent(
        self,
        nlp_result: Dict[str, Any],
        app_state: Any
    ) -> str:
        """Route request to appropriate agent"""
        agent_type = nlp_result["agent_type"]
        entities = nlp_result["entities"]
        intent = nlp_result["intent"]

        try:
            if agent_type == "market":
                return await self._process_market_query(entities, app_state)

            elif agent_type == "strategy":
                return await self._process_strategy_query(entities, intent, app_state)

            elif agent_type == "risk":
                return await self._process_risk_query(entities, app_state)

            else:
                return "I'm not sure how to handle that request yet. Can you try rephrasing?"

        except Exception as e:
            logger.error(f"Agent routing error: {e}")
            return f"I encountered an error with the {agent_type} agent. Please try again."

    async def _process_market_query(
        self,
        entities: Dict[str, Any],
        app_state: Any
    ) -> str:
        """Process market data queries"""
        market_agent = app_state.market_agent

        if not market_agent:
            return "Market data agent is not available right now. Please try again later."

        # Prepare input for market agent
        input_data = {
            "query": "Get current DeFi yield opportunities on Cardano",
            "min_apr": entities.get("target_return", 5.0),
        }

        # Call agent
        result = await market_agent.execute(input_data)

        if result.get("success"):
            # Format response nicely
            opportunities = result.get("opportunities", [])
            if not opportunities:
                return "I couldn't find any yield opportunities matching your criteria right now."

            response = "Here are the top DeFi opportunities on Cardano:\n\n"
            for i, opp in enumerate(opportunities[:5], 1):
                protocol = opp.get("protocol", "Unknown")
                pool = opp.get("pool", "N/A")
                apr = opp.get("apr", 0)
                tvl = opp.get("tvl_ada", 0)
                risk = opp.get("risk_score", 0)

                response += f"{i}. **{protocol}** - {pool}\n"
                response += f"   • APR: {apr}%\n"
                response += f"   • TVL: {tvl:,.0f} ADA\n"
                response += f"   • Risk Score: {risk}/100\n\n"

            response += "\nWould you like me to create a portfolio strategy based on these opportunities?"
            return response
        else:
            return "I couldn't fetch market data right now. Please try again."

    async def _process_strategy_query(
        self,
        entities: Dict[str, Any],
        intent: str,
        app_state: Any
    ) -> str:
        """Process portfolio optimization queries"""
        strategy_agent = app_state.strategy_agent

        if not strategy_agent:
            return "Strategy agent is not available right now. Please try again later."

        # Extract or use defaults
        ada_amount = entities.get("ada_amount", entities.get("numbers", [10000])[0] if entities.get("numbers") else 10000)
        risk_tolerance = entities.get("risk_tolerance", "moderate")
        target_return = entities.get("target_return", 12.0)

        # Prepare input for strategy agent
        input_data = {
            "user_portfolio": {
                "ada_balance": ada_amount,
                "positions": []
            },
            "risk_tolerance": risk_tolerance,
            "target_return": target_return,
            "portfolio_size": ada_amount
        }

        # Call agent
        result = await strategy_agent.execute(input_data)

        if result.get("success"):
            # Format strategy response
            allocations = result.get("recommended_allocations", [])
            expected_apr = result.get("expected_portfolio_apr", 0)
            expected_risk = result.get("expected_portfolio_risk", 0)

            response = f"I've created an optimized strategy for your {ada_amount:,.0f} ADA portfolio:\n\n"
            response += f"**Target:** {risk_tolerance.title()} risk, {target_return}% APR\n"
            response += f"**Expected Results:** {expected_apr}% APR, Risk Score: {expected_risk}/100\n\n"
            response += "**Recommended Allocation:**\n\n"

            for i, alloc in enumerate(allocations, 1):
                protocol = alloc.get("protocol", "Unknown")
                pool = alloc.get("pool", "N/A")
                percent = alloc.get("allocation_percent", 0)
                apr = alloc.get("expected_apr", 0)
                amount = ada_amount * (percent / 100)

                response += f"{i}. **{protocol}** - {pool}\n"
                response += f"   • Allocation: {percent}% ({amount:,.0f} ADA)\n"
                response += f"   • Expected APR: {apr}%\n\n"

            response += "\nWould you like me to assess the risk of this strategy or save it to your portfolio?"
            return response
        else:
            return "I couldn't generate a strategy right now. Please try again."

    async def _process_risk_query(
        self,
        entities: Dict[str, Any],
        app_state: Any
    ) -> str:
        """Process risk assessment queries"""
        risk_agent = app_state.risk_agent

        if not risk_agent:
            return "Risk assessment agent is not available right now. Please try again later."

        # For now, provide general risk info
        # In full implementation, would analyze specific strategy
        input_data = {
            "strategy": {
                "allocations": []  # Would come from context
            }
        }

        result = await risk_agent.execute(input_data)

        if result.get("success"):
            risk_score = result.get("overall_risk_score", 0)
            approved = result.get("approved", True)
            warnings = result.get("warnings", [])
            recommendations = result.get("recommendations", [])

            response = f"**Risk Assessment Results:**\n\n"
            response += f"Overall Risk Score: {risk_score}/100 "
            if risk_score < 30:
                response += "🟢 (Low Risk)\n"
            elif risk_score < 60:
                response += "🟡 (Moderate Risk)\n"
            else:
                response += "🔴 (High Risk)\n"

            response += f"Status: {'✅ Approved' if approved else '❌ Not Recommended'}\n\n"

            if warnings:
                response += "⚠️ **Warnings:**\n"
                for warning in warnings:
                    response += f"• {warning}\n"
                response += "\n"

            if recommendations:
                response += "💡 **Recommendations:**\n"
                for rec in recommendations:
                    response += f"• {rec}\n"

            return response
        else:
            return "I couldn't perform risk assessment right now. Please try again."


# Global chat service instance
_chat_service: Optional[ChatService] = None


def get_chat_service() -> ChatService:
    """Get or create chat service instance"""
    global _chat_service
    if _chat_service is None:
        groq_api_key = os.getenv("GROQ_API_KEY")
        if not groq_api_key:
            raise ValueError("GROQ_API_KEY not set")
        _chat_service = ChatService(groq_api_key)
    return _chat_service

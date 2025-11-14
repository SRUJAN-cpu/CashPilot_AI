"""
Conversation Handler - NLP Layer
Processes natural language inputs and routes to appropriate agents
"""

import re
import logging
from typing import Dict, Any, Optional, List, Tuple
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage

logger = logging.getLogger(__name__)


class ConversationHandler:
    """
    Handles natural language conversation processing

    Features:
    - Intent classification
    - Entity extraction
    - Context tracking
    - Agent routing
    """

    def __init__(self, groq_api_key: str):
        self.llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            api_key=groq_api_key,
            temperature=0.1  # Low temperature for consistent intent classification
        )
        self.conversation_context: Dict[str, Any] = {}

    async def process_message(
        self,
        user_message: str,
        conversation_id: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Dict[str, Any]:
        """
        Process a user message and determine how to respond

        Returns:
            {
                "intent": str,  # optimize_portfolio, market_query, risk_analysis, etc.
                "entities": dict,  # Extracted entities (amounts, risk_level, etc.)
                "agent_type": str,  # Which agent to route to
                "response": str,  # Response to user
                "metadata": dict  # Additional data
            }
        """
        try:
            # Step 1: Classify intent
            intent, confidence = await self._classify_intent(user_message, conversation_history)

            # Step 2: Extract entities
            entities = await self._extract_entities(user_message, intent)

            # Step 3: Determine which agent to route to
            agent_type = self._route_to_agent(intent)

            # Step 4: Generate appropriate response or route to agent
            if confidence < 0.6:
                # Low confidence - ask for clarification
                response = await self._generate_clarification(user_message)
                return {
                    "intent": "clarification",
                    "entities": entities,
                    "agent_type": "general",
                    "response": response,
                    "metadata": {"confidence": confidence}
                }

            # Return intent and routing info for agent processing
            return {
                "intent": intent,
                "entities": entities,
                "agent_type": agent_type,
                "confidence": confidence,
                "metadata": {
                    "conversation_id": conversation_id,
                    "requires_agent": True
                }
            }

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return {
                "intent": "error",
                "entities": {},
                "agent_type": "general",
                "response": "I'm sorry, I encountered an error processing your request. Please try again.",
                "metadata": {"error": str(e)}
            }

    async def _classify_intent(
        self,
        message: str,
        conversation_history: Optional[List[Dict]] = None
    ) -> Tuple[str, float]:
        """
        Classify user intent using LLM

        Returns: (intent, confidence_score)
        """
        system_prompt = """You are an intent classifier for a DeFi portfolio management AI.

Classify user messages into ONE of these intents:
- optimize_portfolio: User wants portfolio optimization/allocation advice
- market_query: User asks about market data, yields, APRs, DEXs
- risk_analysis: User asks about risk, safety, portfolio risk assessment
- portfolio_management: User wants to save, view, update their portfolio
- greeting: User says hi, hello, how are you
- help: User asks what you can do or how to use the system
- other: Doesn't fit above categories

Examples:
"Optimize my 10,000 ADA with moderate risk" -> optimize_portfolio
"What are the best yields on Cardano?" -> market_query
"Is this allocation safe?" -> risk_analysis
"Save this portfolio" -> portfolio_management
"Hello!" -> greeting

Respond with ONLY the intent name and confidence (0-1), format: "intent|confidence"
Example: "optimize_portfolio|0.9"
"""

        context = ""
        if conversation_history and len(conversation_history) > 0:
            recent = conversation_history[-3:]  # Last 3 messages
            context = "Recent conversation:\n" + "\n".join([
                f"{msg['role']}: {msg['content']}" for msg in recent
            ])

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"{context}\n\nUser message: {message}")
        ]

        try:
            response = self.llm.invoke(messages)
            result = response.content.strip()

            # Parse response
            if "|" in result:
                intent, conf_str = result.split("|", 1)
                confidence = float(conf_str)
            else:
                intent = result
                confidence = 0.8

            return intent.strip(), confidence

        except Exception as e:
            logger.error(f"Intent classification error: {e}")
            return "other", 0.5

    async def _extract_entities(self, message: str, intent: str) -> Dict[str, Any]:
        """
        Extract relevant entities from the message
        """
        entities = {}

        # Extract ADA amounts
        ada_pattern = r'(\d+(?:,\d{3})*(?:\.\d+)?)\s*(?:ADA|ada)'
        ada_match = re.search(ada_pattern, message.replace(',', ''))
        if ada_match:
            entities["ada_amount"] = float(ada_match.group(1).replace(',', ''))

        # Extract numbers (could be percentages, amounts, etc.)
        number_pattern = r'\b(\d+(?:,\d{3})*(?:\.\d+)?)\b'
        numbers = re.findall(number_pattern, message.replace(',', ''))
        if numbers:
            entities["numbers"] = [float(n.replace(',', '')) for n in numbers]

        # Extract risk tolerance
        risk_keywords = {
            "conservative": ["conservative", "safe", "low risk", "careful"],
            "moderate": ["moderate", "balanced", "medium risk", "mid"],
            "aggressive": ["aggressive", "high risk", "risky", "bold"]
        }
        message_lower = message.lower()
        for level, keywords in risk_keywords.items():
            if any(kw in message_lower for kw in keywords):
                entities["risk_tolerance"] = level
                break

        # Extract protocol names
        protocols = ["minswap", "sundaeswap", "liqwid", "indigo", "wingriders", "muesliswap"]
        mentioned_protocols = [p for p in protocols if p in message_lower]
        if mentioned_protocols:
            entities["protocols"] = mentioned_protocols

        # Extract target returns
        return_pattern = r'(\d+(?:\.\d+)?)\s*%?\s*(?:APR|apr|return|yield)'
        return_match = re.search(return_pattern, message)
        if return_match:
            entities["target_return"] = float(return_match.group(1))

        return entities

    def _route_to_agent(self, intent: str) -> str:
        """
        Determine which agent should handle this intent
        """
        routing_map = {
            "optimize_portfolio": "strategy",
            "market_query": "market",
            "risk_analysis": "risk",
            "portfolio_management": "strategy",
            "greeting": "general",
            "help": "general",
            "other": "general"
        }
        return routing_map.get(intent, "general")

    async def _generate_clarification(self, message: str) -> str:
        """
        Generate a clarification question when intent is unclear
        """
        system_prompt = """You are a helpful DeFi portfolio assistant.
The user's request is unclear. Ask a friendly clarification question to understand what they want.

Keep it short and natural. Suggest what they might be asking about:
- Portfolio optimization
- Market data and yields
- Risk assessment
- Portfolio management

Example: "I'd be happy to help! Are you looking to optimize your portfolio allocation, check current market yields, or assess portfolio risk?"
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"User said: {message}")
        ]

        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Clarification generation error: {e}")
            return "I'd be happy to help! Could you clarify if you're looking to optimize your portfolio, check market data, or assess risk?"

    async def format_agent_response(
        self,
        agent_response: Dict[str, Any],
        agent_type: str
    ) -> str:
        """
        Format agent response into natural language
        """
        system_prompt = f"""You are a friendly DeFi portfolio assistant.
Convert this {agent_type} agent's JSON response into a natural, conversational message for the user.

Keep it concise but informative. Use emojis sparingly. Format numbers nicely.

Guidelines:
- For market data: Present yields and protocols clearly
- For strategies: Explain the allocation reasoning
- For risk: Highlight key concerns and scores
- Be encouraging but realistic
"""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=f"Agent response: {agent_response}")
        ]

        try:
            response = self.llm.invoke(messages)
            return response.content
        except Exception as e:
            logger.error(f"Response formatting error: {e}")
            # Fallback to simple formatting
            return f"Here's what I found:\n\n{str(agent_response)}"

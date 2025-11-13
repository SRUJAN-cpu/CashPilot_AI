"""
Market Data Tools for LangChain Agent
Provides tools for fetching DeFi protocol data
"""

import logging
from typing import List
from langchain.tools import Tool
from langchain.pydantic_v1 import BaseModel, Field

from ...cardano.defi_protocols import get_defi_manager, Protocol

logger = logging.getLogger(__name__)


class MinswapPoolsInput(BaseModel):
    """Input for getting Minswap pools"""
    pass


class SundaeSwapPoolsInput(BaseModel):
    """Input for getting SundaeSwap pools"""
    pass


class YieldOpportunitiesInput(BaseModel):
    """Input for getting yield opportunities"""
    min_tvl: float = Field(default=100_000, description="Minimum TVL in ADA")
    min_apr: float = Field(default=5.0, description="Minimum APR percentage")


class ProtocolTVLInput(BaseModel):
    """Input for getting protocol TVL"""
    protocol: str = Field(description="Protocol name (minswap, sundaeswap, liqwid)")


class MarketDataTools:
    """
    Collection of tools for fetching Cardano DeFi market data
    Used by Market Intelligence Agent
    """

    def __init__(self):
        self.defi_manager = get_defi_manager()

    async def _get_minswap_pools(self) -> str:
        """Get Minswap liquidity pools data"""
        try:
            pools = await self.defi_manager.get_minswap_pools()

            if not pools:
                return "No Minswap pools found or API unavailable."

            # Format top 10 pools by TVL
            pools_sorted = sorted(pools, key=lambda x: x.tvl_ada, reverse=True)[:10]

            result = "Top 10 Minswap Pools by TVL:\n\n"
            for i, pool in enumerate(pools_sorted, 1):
                result += f"{i}. {pool.token_a}/{pool.token_b}\n"
                result += f"   TVL: {pool.tvl_ada:,.0f} ADA\n"
                result += f"   APR: {pool.apr:.2f}%\n"
                result += f"   24h Volume: {pool.volume_24h:,.0f} ADA\n"
                result += f"   24h Fees: {pool.fees_24h:,.0f} ADA\n\n"

            return result

        except Exception as e:
            logger.error(f"Error fetching Minswap pools: {e}")
            return f"Error fetching Minswap pools: {str(e)}"

    async def _get_sundaeswap_pools(self) -> str:
        """Get SundaeSwap liquidity pools data"""
        try:
            pools = await self.defi_manager.get_sundaeswap_pools()

            if not pools:
                return "No SundaeSwap pools found or API unavailable."

            pools_sorted = sorted(pools, key=lambda x: x.tvl_ada, reverse=True)[:10]

            result = "Top 10 SundaeSwap Pools by TVL:\n\n"
            for i, pool in enumerate(pools_sorted, 1):
                result += f"{i}. {pool.token_a}/{pool.token_b}\n"
                result += f"   TVL: {pool.tvl_ada:,.0f} ADA\n"
                result += f"   APR: {pool.apr:.2f}%\n"
                result += f"   24h Volume: {pool.volume_24h:,.0f} ADA\n\n"

            return result

        except Exception as e:
            logger.error(f"Error fetching SundaeSwap pools: {e}")
            return f"Error fetching SundaeSwap pools: {str(e)}"

    async def _get_yield_opportunities(self, min_tvl: float, min_apr: float) -> str:
        """Get best yield opportunities across protocols"""
        try:
            opportunities = await self.defi_manager.get_best_yield_opportunities(
                min_tvl=min_tvl,
                min_apr=min_apr
            )

            if not opportunities:
                return f"No yield opportunities found with TVL >= {min_tvl:,.0f} ADA and APR >= {min_apr}%"

            result = f"Best Yield Opportunities (TVL >= {min_tvl:,.0f} ADA, APR >= {min_apr}%):\n\n"

            for i, opp in enumerate(opportunities[:15], 1):
                result += f"{i}. {opp['protocol'].upper()}"

                if opp['type'] == 'liquidity_pool':
                    result += f" - {opp['pair']}\n"
                    result += f"   APR: {opp['apr']:.2f}%\n"
                    result += f"   TVL: {opp['tvl_ada']:,.0f} ADA\n"
                    result += f"   Risk Score: {opp['risk_score']:.1f}/100\n"
                else:
                    result += f" - Lending {opp['asset']}\n"
                    result += f"   Supply APR: {opp['apr']:.2f}%\n"
                    result += f"   Utilization: {opp.get('utilization', 0)*100:.1f}%\n"
                    result += f"   Risk Score: {opp['risk_score']:.1f}/100\n"

                result += "\n"

            return result

        except Exception as e:
            logger.error(f"Error fetching yield opportunities: {e}")
            return f"Error fetching yield opportunities: {str(e)}"

    async def _get_protocol_tvl(self, protocol: str) -> str:
        """Get total value locked for a protocol"""
        try:
            protocol_map = {
                "minswap": Protocol.MINSWAP,
                "sundaeswap": Protocol.SUNDAESWAP,
                "liqwid": Protocol.LIQWID
            }

            protocol_enum = protocol_map.get(protocol.lower())
            if not protocol_enum:
                return f"Unknown protocol: {protocol}. Supported: minswap, sundaeswap, liqwid"

            tvl = await self.defi_manager.get_protocol_tvl(protocol_enum)

            return f"{protocol.upper()} Total Value Locked: {tvl:,.0f} ADA (${tvl * 0.35:,.0f} USD approx)"

        except Exception as e:
            logger.error(f"Error fetching protocol TVL: {e}")
            return f"Error fetching protocol TVL: {str(e)}"

    def get_langchain_tools(self) -> List[Tool]:
        """
        Get LangChain Tool objects for the agent

        Returns:
            List of Tool objects
        """
        return [
            Tool(
                name="get_minswap_pools",
                description="Get top Minswap DEX liquidity pools with TVL, APR, volume, and fees data",
                func=lambda x: self._get_minswap_pools(),
                coroutine=self._get_minswap_pools
            ),
            Tool(
                name="get_sundaeswap_pools",
                description="Get top SundaeSwap DEX liquidity pools with TVL, APR, and volume data",
                func=lambda x: self._get_sundaeswap_pools(),
                coroutine=self._get_sundaeswap_pools
            ),
            Tool(
                name="get_yield_opportunities",
                description="Find best yield opportunities across all Cardano DeFi protocols with filters for minimum TVL and APR",
                func=lambda x: self._get_yield_opportunities(
                    min_tvl=float(x.get("min_tvl", 100_000)),
                    min_apr=float(x.get("min_apr", 5.0))
                ),
                coroutine=self._get_yield_opportunities,
                args_schema=YieldOpportunitiesInput
            ),
            Tool(
                name="get_protocol_tvl",
                description="Get total value locked (TVL) for a specific DeFi protocol (minswap, sundaeswap, liqwid)",
                func=lambda protocol: self._get_protocol_tvl(protocol),
                coroutine=self._get_protocol_tvl,
                args_schema=ProtocolTVLInput
            )
        ]

    async def close(self):
        """Cleanup resources"""
        await self.defi_manager.close()

"""
DeFi Protocol Integration for Cardano
Provides yield data and protocol information for Minswap, SundaeSwap, Indigo, Liqwid
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ProtocolType(str, Enum):
    """DeFi protocol types"""
    DEX = "dex"
    LENDING = "lending"
    LIQUID_STAKING = "liquid_staking"
    STABLE_COIN = "stable_coin"


class Protocol(str, Enum):
    """Supported Cardano DeFi protocols"""
    MINSWAP = "minswap"
    SUNDAESWAP = "sundaeswap"
    INDIGO = "indigo"
    LIQWID = "liqwid"
    MUESLISWAP = "muesliswap"
    WINGRIDERS = "wingriders"


class PoolData(BaseModel):
    """Liquidity pool data"""
    pool_id: str
    protocol: Protocol
    token_a: str
    token_b: str
    token_a_reserve: float
    token_b_reserve: float
    tvl_ada: float
    apr: float
    volume_24h: float
    fees_24h: float
    last_updated: datetime


class LendingData(BaseModel):
    """Lending protocol data"""
    protocol: Protocol
    asset: str
    supply_apr: float
    borrow_apr: float
    total_supply: float
    total_borrowed: float
    utilization_rate: float
    collateral_factor: float
    last_updated: datetime


class DeFiProtocolManager:
    """
    Manages connections to Cardano DeFi protocols
    Fetches yield rates, TVL, and other DeFi metrics
    """

    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def get_minswap_pools(self) -> List[PoolData]:
        """
        Get Minswap DEX pools and yield data

        Returns:
            List of pool data
        """
        try:
            # Minswap API endpoint
            response = await self.client.get(
                "https://api.minswap.org/pools"
            )
            response.raise_for_status()
            data = response.json()

            pools = []
            for pool in data:
                pools.append(PoolData(
                    pool_id=pool.get("id", ""),
                    protocol=Protocol.MINSWAP,
                    token_a=pool.get("tokenA", {}).get("symbol", "ADA"),
                    token_b=pool.get("tokenB", {}).get("symbol", ""),
                    token_a_reserve=float(pool.get("reserveA", 0)) / 1_000_000,
                    token_b_reserve=float(pool.get("reserveB", 0)) / 1_000_000,
                    tvl_ada=float(pool.get("tvl", 0)) / 1_000_000,
                    apr=float(pool.get("apr", 0)),
                    volume_24h=float(pool.get("volume24h", 0)) / 1_000_000,
                    fees_24h=float(pool.get("fees24h", 0)) / 1_000_000,
                    last_updated=datetime.now()
                ))

            logger.info(f"Fetched {len(pools)} Minswap pools")
            return pools

        except Exception as e:
            logger.error(f"Failed to fetch Minswap pools: {e}")
            return []

    async def get_sundaeswap_pools(self) -> List[PoolData]:
        """
        Get SundaeSwap DEX pools and yield data

        Returns:
            List of pool data
        """
        try:
            # SundaeSwap API endpoint
            response = await self.client.get(
                "https://api.sundaeswap.finance/pools"
            )
            response.raise_for_status()
            data = response.json()

            pools = []
            for pool in data.get("pools", []):
                pools.append(PoolData(
                    pool_id=pool.get("poolId", ""),
                    protocol=Protocol.SUNDAESWAP,
                    token_a=pool.get("assetA", {}).get("ticker", "ADA"),
                    token_b=pool.get("assetB", {}).get("ticker", ""),
                    token_a_reserve=float(pool.get("quantityA", 0)) / 1_000_000,
                    token_b_reserve=float(pool.get("quantityB", 0)) / 1_000_000,
                    tvl_ada=float(pool.get("tvl", 0)) / 1_000_000,
                    apr=float(pool.get("apr", 0)),
                    volume_24h=float(pool.get("volume24h", 0)) / 1_000_000,
                    fees_24h=float(pool.get("fees24h", 0)) / 1_000_000,
                    last_updated=datetime.now()
                ))

            logger.info(f"Fetched {len(pools)} SundaeSwap pools")
            return pools

        except Exception as e:
            logger.error(f"Failed to fetch SundaeSwap pools: {e}")
            return []

    async def get_liqwid_markets(self) -> List[LendingData]:
        """
        Get Liqwid lending markets data

        Returns:
            List of lending market data
        """
        try:
            # Liqwid API endpoint (placeholder - adjust based on actual API)
            response = await self.client.get(
                "https://api.liqwid.finance/v1/markets"
            )
            response.raise_for_status()
            data = response.json()

            markets = []
            for market in data.get("markets", []):
                markets.append(LendingData(
                    protocol=Protocol.LIQWID,
                    asset=market.get("asset", ""),
                    supply_apr=float(market.get("supplyApr", 0)),
                    borrow_apr=float(market.get("borrowApr", 0)),
                    total_supply=float(market.get("totalSupply", 0)),
                    total_borrowed=float(market.get("totalBorrowed", 0)),
                    utilization_rate=float(market.get("utilizationRate", 0)),
                    collateral_factor=float(market.get("collateralFactor", 0)),
                    last_updated=datetime.now()
                ))

            logger.info(f"Fetched {len(markets)} Liqwid markets")
            return markets

        except Exception as e:
            logger.error(f"Failed to fetch Liqwid markets: {e}")
            return []

    async def get_best_yield_opportunities(
        self,
        min_tvl: float = 100_000,
        min_apr: float = 5.0
    ) -> List[Dict[str, Any]]:
        """
        Find best yield opportunities across all protocols

        Args:
            min_tvl: Minimum TVL in ADA
            min_apr: Minimum APR percentage

        Returns:
            List of top opportunities sorted by APR
        """
        opportunities = []

        # Fetch all DEX pools
        minswap_pools = await self.get_minswap_pools()
        sundae_pools = await self.get_sundaeswap_pools()

        all_pools = minswap_pools + sundae_pools

        # Filter and sort
        for pool in all_pools:
            if pool.tvl_ada >= min_tvl and pool.apr >= min_apr:
                opportunities.append({
                    "type": "liquidity_pool",
                    "protocol": pool.protocol.value,
                    "pool_id": pool.pool_id,
                    "pair": f"{pool.token_a}/{pool.token_b}",
                    "apr": pool.apr,
                    "tvl_ada": pool.tvl_ada,
                    "risk_score": self._calculate_risk_score(pool)
                })

        # Fetch lending markets
        liqwid_markets = await self.get_liqwid_markets()

        for market in liqwid_markets:
            if market.supply_apr >= min_apr:
                opportunities.append({
                    "type": "lending",
                    "protocol": Protocol.LIQWID.value,
                    "asset": market.asset,
                    "apr": market.supply_apr,
                    "total_supply": market.total_supply,
                    "utilization": market.utilization_rate,
                    "risk_score": self._calculate_lending_risk(market)
                })

        # Sort by APR descending
        opportunities.sort(key=lambda x: x["apr"], reverse=True)

        logger.info(f"Found {len(opportunities)} yield opportunities")
        return opportunities

    def _calculate_risk_score(self, pool: PoolData) -> float:
        """
        Calculate risk score for a liquidity pool (0-100, lower is safer)

        Args:
            pool: Pool data

        Returns:
            Risk score
        """
        risk = 0.0

        # TVL risk (lower TVL = higher risk)
        if pool.tvl_ada < 50_000:
            risk += 30
        elif pool.tvl_ada < 100_000:
            risk += 20
        elif pool.tvl_ada < 500_000:
            risk += 10

        # APR risk (unusually high APR = higher risk)
        if pool.apr > 100:
            risk += 30
        elif pool.apr > 50:
            risk += 20
        elif pool.apr > 30:
            risk += 10

        # Volume risk (low volume = higher risk)
        if pool.volume_24h < 10_000:
            risk += 20
        elif pool.volume_24h < 50_000:
            risk += 10

        return min(risk, 100.0)

    def _calculate_lending_risk(self, market: LendingData) -> float:
        """
        Calculate risk score for lending market (0-100, lower is safer)

        Args:
            market: Lending market data

        Returns:
            Risk score
        """
        risk = 0.0

        # Utilization risk (very high utilization = risk of illiquidity)
        if market.utilization_rate > 0.95:
            risk += 40
        elif market.utilization_rate > 0.85:
            risk += 25
        elif market.utilization_rate > 0.75:
            risk += 10

        # APR risk (unusually high = higher risk)
        if market.supply_apr > 50:
            risk += 30
        elif market.supply_apr > 30:
            risk += 15

        # Collateral factor risk (low collateral = higher risk)
        if market.collateral_factor < 0.5:
            risk += 20
        elif market.collateral_factor < 0.7:
            risk += 10

        return min(risk, 100.0)

    async def get_protocol_tvl(self, protocol: Protocol) -> float:
        """
        Get total value locked for a protocol

        Args:
            protocol: Protocol to query

        Returns:
            TVL in ADA
        """
        if protocol == Protocol.MINSWAP:
            pools = await self.get_minswap_pools()
            return sum(pool.tvl_ada for pool in pools)
        elif protocol == Protocol.SUNDAESWAP:
            pools = await self.get_sundaeswap_pools()
            return sum(pool.tvl_ada for pool in pools)
        elif protocol == Protocol.LIQWID:
            markets = await self.get_liqwid_markets()
            return sum(market.total_supply for market in markets)
        else:
            return 0.0

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Singleton instance
_defi_manager: Optional[DeFiProtocolManager] = None


def get_defi_manager() -> DeFiProtocolManager:
    """Get or create DeFiProtocolManager singleton"""
    global _defi_manager

    if _defi_manager is None:
        _defi_manager = DeFiProtocolManager()

    return _defi_manager

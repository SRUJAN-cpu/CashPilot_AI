"""
Risk Analysis Models
Implements risk scoring and validation logic
"""

import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)


class RiskAnalyzer:
    """
    Risk analysis engine for portfolio strategies and transactions
    """

    def __init__(self):
        # Protocol risk ratings (0-100, lower is safer)
        self.protocol_risk_ratings = {
            "minswap": 25,  # Well-established, high TVL
            "sundaeswap": 30,  # Established DEX
            "liqwid": 35,  # Lending protocol, inherent risk
            "indigo": 40,  # Stable coin protocol
            "muesliswap": 35,
            "wingriders": 30
        }

        # Risk thresholds
        self.risk_thresholds = {
            "max_concentration": 50,  # % in single protocol
            "min_tvl": 100_000,  # Minimum protocol TVL
            "max_risk_score": 70,  # Overall risk score limit
            "max_apr": 100  # Unusually high APR warning
        }

    def analyze_strategy(self, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze risk of a portfolio strategy

        Args:
            strategy: Strategy to analyze

        Returns:
            Risk analysis report
        """
        try:
            allocations = strategy.get("recommended_allocations", [])

            # Calculate various risk metrics
            concentration_risk = self._calculate_concentration_risk(allocations)
            protocol_risk = self._calculate_protocol_risk(allocations)
            apr_risk = self._calculate_apr_risk(allocations)
            diversification_score = self._calculate_diversification(allocations)

            # Overall risk score (weighted average)
            overall_risk = (
                concentration_risk * 0.3 +
                protocol_risk * 0.4 +
                apr_risk * 0.3
            )

            # Generate warnings
            warnings = []
            if concentration_risk > 60:
                warnings.append("High concentration risk: Portfolio not well diversified")

            if protocol_risk > 50:
                warnings.append("High protocol risk: Consider safer protocols")

            if apr_risk > 60:
                warnings.append("Unusually high APRs detected: Possible high risk")

            # Recommendations
            recommendations = []
            if concentration_risk > 40:
                recommendations.append("Increase diversification across protocols")

            if overall_risk > 50:
                recommendations.append("Consider reducing risk exposure")

            analysis = {
                "overall_risk_score": round(overall_risk, 1),
                "concentration_risk": round(concentration_risk, 1),
                "protocol_risk": round(protocol_risk, 1),
                "apr_risk": round(apr_risk, 1),
                "diversification_score": round(diversification_score, 1),
                "warnings": warnings,
                "recommendations": recommendations,
                "risk_breakdown": {
                    "concentration": f"{concentration_risk:.1f}/100",
                    "protocol_safety": f"{protocol_risk:.1f}/100",
                    "yield_risk": f"{apr_risk:.1f}/100"
                }
            }

            logger.info(f"Strategy risk analysis: Overall score {overall_risk:.1f}/100")
            return analysis

        except Exception as e:
            logger.error(f"Failed to analyze strategy risk: {e}")
            raise

    def _calculate_concentration_risk(
        self,
        allocations: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate concentration risk (0-100)
        Higher score = more concentrated (riskier)
        """
        if not allocations:
            return 0.0

        # Find max allocation percentage
        max_allocation = max(
            alloc.get("allocation_percent", 0) for alloc in allocations
        )

        # Calculate Herfindahl-Hirschman Index (HHI) for concentration
        hhi = sum(
            (alloc.get("allocation_percent", 0) ** 2)
            for alloc in allocations
        )

        # Normalize to 0-100 scale
        # HHI ranges from 0 (perfectly diversified) to 10000 (fully concentrated)
        concentration_risk = (hhi / 100)

        return min(concentration_risk, 100.0)

    def _calculate_protocol_risk(
        self,
        allocations: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate weighted average protocol risk
        """
        if not allocations:
            return 0.0

        total_risk = 0.0
        total_weight = 0.0

        for alloc in allocations:
            protocol = alloc.get("protocol", "").lower()
            weight = alloc.get("allocation_percent", 0) / 100

            # Get protocol base risk
            base_risk = self.protocol_risk_ratings.get(protocol, 50)

            # Adjust for individual position risk
            position_risk = alloc.get("risk_score", base_risk)

            total_risk += position_risk * weight
            total_weight += weight

        if total_weight == 0:
            return 0.0

        return total_risk / total_weight

    def _calculate_apr_risk(
        self,
        allocations: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate risk based on APR levels
        Unusually high APR often indicates higher risk
        """
        if not allocations:
            return 0.0

        risk_scores = []

        for alloc in allocations:
            apr = alloc.get("expected_apr", 0)

            # Risk score based on APR thresholds
            if apr > 100:
                risk_scores.append(80)  # Very high risk
            elif apr > 50:
                risk_scores.append(60)
            elif apr > 30:
                risk_scores.append(40)
            elif apr > 15:
                risk_scores.append(20)
            else:
                risk_scores.append(10)  # Conservative APR

        return sum(risk_scores) / len(risk_scores) if risk_scores else 0.0

    def _calculate_diversification(
        self,
        allocations: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate diversification score (0-100, higher is better)
        """
        if not allocations:
            return 0.0

        num_positions = len(allocations)

        # Number of different protocols
        protocols = set(alloc.get("protocol") for alloc in allocations)
        num_protocols = len(protocols)

        # Balance of allocations
        if num_positions == 1:
            balance_score = 0
        else:
            # Calculate how evenly distributed allocations are
            allocations_pct = [alloc.get("allocation_percent", 0) for alloc in allocations]
            ideal_allocation = 100 / num_positions
            variance = sum((pct - ideal_allocation) ** 2 for pct in allocations_pct) / num_positions
            balance_score = max(0, 100 - variance)

        # Combine factors
        diversification = (
            (num_protocols / 5) * 40 +  # Protocol diversity (max 5 protocols = 40 points)
            (num_positions / 5) * 30 +  # Position count (max 5 positions = 30 points)
            (balance_score / 100) * 30   # Balance (30 points)
        )

        return min(diversification, 100.0)

    def analyze_portfolio_health(
        self,
        portfolio: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze health of existing portfolio

        Args:
            portfolio: Current portfolio holdings

        Returns:
            Health metrics
        """
        try:
            positions = portfolio.get("positions", [])

            concentration_risk = self._calculate_concentration_risk(positions)
            liquidity_risk = self._calculate_liquidity_risk(positions)
            overall_health = 100 - (concentration_risk * 0.5 + liquidity_risk * 0.5)

            return {
                "overall_health_score": round(overall_health, 1),
                "concentration_risk": round(concentration_risk, 1),
                "liquidity_risk": round(liquidity_risk, 1),
                "num_positions": len(positions),
                "total_value_ada": sum(pos.get("value_ada", 0) for pos in positions)
            }

        except Exception as e:
            logger.error(f"Failed to analyze portfolio health: {e}")
            return {
                "overall_health_score": 0,
                "error": str(e)
            }

    def _calculate_liquidity_risk(
        self,
        positions: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate liquidity risk based on TVL and volume
        """
        if not positions:
            return 0.0

        risk_scores = []

        for pos in positions:
            tvl = pos.get("tvl_ada", 0)
            volume_24h = pos.get("volume_24h", 0)

            # TVL risk
            if tvl < 50_000:
                tvl_risk = 80
            elif tvl < 100_000:
                tvl_risk = 60
            elif tvl < 500_000:
                tvl_risk = 40
            else:
                tvl_risk = 20

            # Volume risk
            if volume_24h < 10_000:
                volume_risk = 60
            elif volume_24h < 50_000:
                volume_risk = 30
            else:
                volume_risk = 10

            position_risk = (tvl_risk + volume_risk) / 2
            risk_scores.append(position_risk)

        return sum(risk_scores) / len(risk_scores) if risk_scores else 0.0

    def validate_transaction(
        self,
        transaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate a transaction for safety

        Args:
            transaction: Transaction to validate

        Returns:
            Validation result
        """
        try:
            tx_type = transaction.get("type", "")
            amount = transaction.get("amount", 0)
            protocol = transaction.get("protocol", "").lower()

            warnings = []
            risk_score = 30  # Base risk

            # Protocol risk
            protocol_risk = self.protocol_risk_ratings.get(protocol, 50)
            risk_score += protocol_risk * 0.5

            # Amount risk (large transactions = higher risk)
            if amount > 100_000:
                warnings.append("Large transaction amount")
                risk_score += 20
            elif amount > 50_000:
                risk_score += 10

            # Transaction type risk
            if tx_type in ["swap", "add_liquidity"]:
                risk_score += 10
            elif tx_type == "lending_supply":
                risk_score += 15

            # Approval
            approved = risk_score <= 70

            return {
                "approved": approved,
                "risk_score": round(risk_score, 1),
                "warnings": warnings
            }

        except Exception as e:
            logger.error(f"Failed to validate transaction: {e}")
            return {
                "approved": False,
                "risk_score": 100,
                "warnings": [f"Validation error: {str(e)}"]
            }

"""
Wallet Manager for Masumi Agent Wallets
Handles wallet creation, funding, and balance checks
"""

import os
import logging
from typing import Dict, Optional
from dataclasses import dataclass
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class WalletInfo(BaseModel):
    """Wallet information model"""
    wallet_id: str
    address: str
    balance: float = 0.0
    network: str = "preprod"


@dataclass
class WalletManager:
    """
    Manages Cardano wallets for Masumi agents
    Integrates with Masumi Payment Service for wallet operations
    """

    payment_service_url: str
    network: str = "preprod"

    def __post_init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)

    async def create_wallet(self, agent_name: str) -> WalletInfo:
        """
        Create a new wallet for an agent via Masumi Payment Service

        Args:
            agent_name: Name of the agent (e.g., "market_intelligence")

        Returns:
            WalletInfo with wallet_id and address
        """
        try:
            response = await self.client.post(
                f"{self.payment_service_url}/wallet/create",
                json={
                    "name": agent_name,
                    "network": self.network
                }
            )
            response.raise_for_status()
            data = response.json()

            wallet = WalletInfo(
                wallet_id=data["wallet_id"],
                address=data["address"],
                network=self.network
            )

            logger.info(f"Created wallet for {agent_name}: {wallet.address}")
            return wallet

        except httpx.HTTPError as e:
            logger.error(f"Failed to create wallet for {agent_name}: {e}")
            raise

    async def get_balance(self, wallet_id: str) -> float:
        """
        Get wallet balance in ADA

        Args:
            wallet_id: Masumi wallet ID

        Returns:
            Balance in ADA
        """
        try:
            response = await self.client.get(
                f"{self.payment_service_url}/wallet/{wallet_id}/balance"
            )
            response.raise_for_status()
            data = response.json()

            # Convert lovelace to ADA (1 ADA = 1,000,000 lovelace)
            balance_ada = data.get("balance", 0) / 1_000_000
            return balance_ada

        except httpx.HTTPError as e:
            logger.error(f"Failed to get balance for wallet {wallet_id}: {e}")
            return 0.0

    async def get_wallet_info(self, wallet_id: str) -> Optional[WalletInfo]:
        """
        Get complete wallet information

        Args:
            wallet_id: Masumi wallet ID

        Returns:
            WalletInfo or None if not found
        """
        try:
            response = await self.client.get(
                f"{self.payment_service_url}/wallet/{wallet_id}"
            )
            response.raise_for_status()
            data = response.json()

            balance = await self.get_balance(wallet_id)

            return WalletInfo(
                wallet_id=wallet_id,
                address=data["address"],
                balance=balance,
                network=data.get("network", self.network)
            )

        except httpx.HTTPError as e:
            logger.error(f"Failed to get wallet info for {wallet_id}: {e}")
            return None

    async def fund_wallet(self, address: str, amount_ada: float) -> bool:
        """
        Request test ADA from faucet (preprod only)

        Args:
            address: Wallet address to fund
            amount_ada: Amount in ADA to request

        Returns:
            True if successful
        """
        if self.network != "preprod":
            logger.warning("Faucet funding only available on preprod network")
            return False

        try:
            # Use Cardano testnet faucet API
            faucet_url = "https://faucet.preprod.world.dev.cardano.org/send-money"
            response = await self.client.post(
                faucet_url,
                json={"address": address}
            )
            response.raise_for_status()

            logger.info(f"Requested {amount_ada} test ADA for {address}")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to fund wallet {address}: {e}")
            return False

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Singleton instance for easy access
_wallet_manager: Optional[WalletManager] = None


def get_wallet_manager() -> WalletManager:
    """Get or create WalletManager singleton"""
    global _wallet_manager

    if _wallet_manager is None:
        payment_url = os.getenv("MASUMI_PAYMENT_SERVICE_URL", "http://localhost:8080/payment")
        network = os.getenv("CARDANO_NETWORK", "preprod")
        _wallet_manager = WalletManager(
            payment_service_url=payment_url,
            network=network
        )

    return _wallet_manager

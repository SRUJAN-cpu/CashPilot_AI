"""
Blockfrost API Client for Cardano Data
Provides blockchain queries and transaction submission
"""

import os
import logging
from typing import Optional, Dict, Any, List
from blockfrost import BlockFrostApi, ApiError, ApiUrls
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class AddressInfo(BaseModel):
    """Cardano address information"""
    address: str
    balance: int  # in lovelace
    stake_address: Optional[str] = None
    script: bool = False


class TransactionInfo(BaseModel):
    """Transaction information"""
    tx_hash: str
    block: str
    block_height: int
    slot: int
    index: int
    output_amount: List[Dict[str, Any]]
    fees: int
    deposit: int
    size: int
    invalid_before: Optional[int] = None
    invalid_hereafter: Optional[int] = None


class PoolInfo(BaseModel):
    """Stake pool information"""
    pool_id: str
    hex: str
    vrf_key: str
    blocks_minted: int
    live_stake: int
    live_size: float
    live_saturation: float
    active_stake: int
    active_size: float


class BlockfrostClient:
    """
    Blockfrost API client for Cardano blockchain data
    Provides access to addresses, transactions, pools, and more
    """

    def __init__(
        self,
        project_id: Optional[str] = None,
        network: str = "preprod"
    ):
        self.project_id = project_id or os.getenv("BLOCKFROST_PROJECT_ID")
        if not self.project_id:
            raise ValueError("BLOCKFROST_PROJECT_ID not set")

        # Set network
        if network == "mainnet":
            base_url = ApiUrls.mainnet.value
        elif network == "preprod":
            base_url = ApiUrls.preprod.value
        else:
            base_url = ApiUrls.testnet.value

        self.api = BlockFrostApi(
            project_id=self.project_id,
            base_url=base_url
        )
        self.network = network
        logger.info(f"Initialized Blockfrost client for {network}")

    async def get_address_info(self, address: str) -> Optional[AddressInfo]:
        """
        Get information about a Cardano address

        Args:
            address: Cardano address

        Returns:
            AddressInfo or None if not found
        """
        try:
            data = self.api.address(address)

            return AddressInfo(
                address=data.address,
                balance=int(data.amount[0].quantity) if data.amount else 0,
                stake_address=data.stake_address,
                script=data.script
            )

        except ApiError as e:
            logger.error(f"Failed to get address info for {address}: {e}")
            return None

    async def get_address_balance(self, address: str) -> int:
        """
        Get address balance in lovelace

        Args:
            address: Cardano address

        Returns:
            Balance in lovelace (1 ADA = 1,000,000 lovelace)
        """
        info = await self.get_address_info(address)
        return info.balance if info else 0

    async def get_address_utxos(self, address: str) -> List[Dict[str, Any]]:
        """
        Get UTXOs for an address

        Args:
            address: Cardano address

        Returns:
            List of UTXO objects
        """
        try:
            utxos = self.api.address_utxos(address)
            return [
                {
                    "tx_hash": utxo.tx_hash,
                    "output_index": utxo.output_index,
                    "amount": utxo.amount,
                    "block": utxo.block,
                    "data_hash": utxo.data_hash
                }
                for utxo in utxos
            ]

        except ApiError as e:
            logger.error(f"Failed to get UTXOs for {address}: {e}")
            return []

    async def get_transaction(self, tx_hash: str) -> Optional[TransactionInfo]:
        """
        Get transaction details

        Args:
            tx_hash: Transaction hash

        Returns:
            TransactionInfo or None if not found
        """
        try:
            tx = self.api.transaction(tx_hash)

            return TransactionInfo(
                tx_hash=tx.hash,
                block=tx.block,
                block_height=tx.block_height,
                slot=tx.slot,
                index=tx.index,
                output_amount=[
                    {"unit": amt.unit, "quantity": amt.quantity}
                    for amt in tx.output_amount
                ],
                fees=int(tx.fees),
                deposit=int(tx.deposit),
                size=tx.size,
                invalid_before=tx.invalid_before,
                invalid_hereafter=tx.invalid_hereafter
            )

        except ApiError as e:
            logger.error(f"Failed to get transaction {tx_hash}: {e}")
            return None

    async def submit_transaction(self, tx_cbor: str) -> Optional[str]:
        """
        Submit a signed transaction to the blockchain

        Args:
            tx_cbor: Transaction CBOR hex string

        Returns:
            Transaction hash if successful, None otherwise
        """
        try:
            result = self.api.transaction_submit(tx_cbor)
            logger.info(f"Transaction submitted: {result}")
            return result

        except ApiError as e:
            logger.error(f"Failed to submit transaction: {e}")
            return None

    async def get_latest_block(self) -> Optional[Dict[str, Any]]:
        """
        Get latest block information

        Returns:
            Block data
        """
        try:
            block = self.api.block_latest()
            return {
                "hash": block.hash,
                "epoch": block.epoch,
                "slot": block.slot,
                "height": block.height,
                "time": block.time,
                "tx_count": block.tx_count,
                "size": block.size
            }

        except ApiError as e:
            logger.error(f"Failed to get latest block: {e}")
            return None

    async def get_epoch_parameters(self) -> Optional[Dict[str, Any]]:
        """
        Get current epoch protocol parameters

        Returns:
            Protocol parameters
        """
        try:
            params = self.api.epoch_latest_parameters()
            return {
                "min_fee_a": params.min_fee_a,
                "min_fee_b": params.min_fee_b,
                "max_tx_size": params.max_tx_size,
                "max_block_header_size": params.max_block_header_size,
                "key_deposit": params.key_deposit,
                "pool_deposit": params.pool_deposit,
                "protocol_major_ver": params.protocol_major_ver,
                "protocol_minor_ver": params.protocol_minor_ver
            }

        except ApiError as e:
            logger.error(f"Failed to get epoch parameters: {e}")
            return None

    async def get_pool_info(self, pool_id: str) -> Optional[PoolInfo]:
        """
        Get stake pool information

        Args:
            pool_id: Pool ID

        Returns:
            PoolInfo or None
        """
        try:
            pool = self.api.pool(pool_id)

            return PoolInfo(
                pool_id=pool.pool_id,
                hex=pool.hex,
                vrf_key=pool.vrf_key,
                blocks_minted=pool.blocks_minted,
                live_stake=int(pool.live_stake),
                live_size=pool.live_size,
                live_saturation=pool.live_saturation,
                active_stake=int(pool.active_stake),
                active_size=pool.active_size
            )

        except ApiError as e:
            logger.error(f"Failed to get pool info for {pool_id}: {e}")
            return None


# Singleton instance
_blockfrost_client: Optional[BlockfrostClient] = None


def get_blockfrost_client() -> BlockfrostClient:
    """Get or create BlockfrostClient singleton"""
    global _blockfrost_client

    if _blockfrost_client is None:
        network = os.getenv("CARDANO_NETWORK", "preprod")
        _blockfrost_client = BlockfrostClient(network=network)

    return _blockfrost_client

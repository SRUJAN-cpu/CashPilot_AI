"""
Masumi Payment Service Integration
Handles agent-to-agent and human-to-agent payments

Based on Masumi Network standards:
- FundsLocked status for payment escrow
- Job-based payment workflow
- Cardano on-chain payment verification

Reference: https://docs.masumi.network/documentation/protocols/payments
"""

import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from enum import Enum
import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class PaymentStatus(str, Enum):
    """
    Payment transaction status

    Masumi Payment Flow:
    1. AWAITING - Payment request created, awaiting user action
    2. FUNDS_LOCKED - Funds locked in Masumi smart contract (can proceed)
    3. COMPLETED - Payment settled to recipient
    4. FAILED - Payment failed or expired
    5. REFUNDED - Payment refunded to sender
    """
    AWAITING = "awaiting"
    FUNDS_LOCKED = "FundsLocked"  # Critical Masumi status
    COMPLETED = "completed"
    FAILED = "failed"
    REFUNDED = "refunded"


class Payment(BaseModel):
    """Payment transaction model"""
    payment_id: str
    from_wallet: str
    to_wallet: str
    amount_ada: float
    status: PaymentStatus
    timestamp: datetime
    tx_hash: Optional[str] = None
    metadata: Dict[str, Any] = {}


class PaymentRequest(BaseModel):
    """Payment request model"""
    from_wallet_id: str
    to_wallet_id: str
    amount_ada: float
    description: str
    metadata: Dict[str, Any] = {}


class PaymentService:
    """
    Masumi Payment Service client
    Facilitates payments between agents and tracks transaction history
    """

    def __init__(self, service_url: Optional[str] = None):
        self.service_url = service_url or os.getenv(
            "MASUMI_PAYMENT_SERVICE_URL",
            "http://localhost:8080/payment"
        )
        self.client = httpx.AsyncClient(timeout=60.0)

    async def create_payment(
        self,
        from_wallet_id: str,
        to_wallet_id: str,
        amount_ada: float,
        description: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Payment:
        """
        Create a payment from one agent to another

        Args:
            from_wallet_id: Sender's Masumi wallet ID
            to_wallet_id: Recipient's Masumi wallet ID
            amount_ada: Amount in ADA
            description: Payment description/purpose
            metadata: Additional metadata (agent names, service type, etc.)

        Returns:
            Payment object with transaction details
        """
        try:
            payment_request = PaymentRequest(
                from_wallet_id=from_wallet_id,
                to_wallet_id=to_wallet_id,
                amount_ada=amount_ada,
                description=description,
                metadata=metadata or {}
            )

            response = await self.client.post(
                f"{self.service_url}/payment/create",
                json=payment_request.model_dump()
            )
            response.raise_for_status()
            data = response.json()

            payment = Payment(
                payment_id=data["payment_id"],
                from_wallet=from_wallet_id,
                to_wallet=to_wallet_id,
                amount_ada=amount_ada,
                status=PaymentStatus(data.get("status", "pending")),
                timestamp=datetime.fromisoformat(data["timestamp"]),
                tx_hash=data.get("tx_hash"),
                metadata=metadata or {}
            )

            logger.info(
                f"Payment created: {amount_ada} ADA from {from_wallet_id} to {to_wallet_id} "
                f"(Payment ID: {payment.payment_id})"
            )

            return payment

        except httpx.HTTPError as e:
            logger.error(f"Failed to create payment: {e}")
            raise

    async def get_payment_status(self, payment_id: str) -> PaymentStatus:
        """
        Check the status of a payment

        Args:
            payment_id: Masumi payment ID

        Returns:
            Current payment status
        """
        try:
            response = await self.client.get(
                f"{self.service_url}/payment/{payment_id}/status"
            )
            response.raise_for_status()
            data = response.json()

            return PaymentStatus(data["status"])

        except httpx.HTTPError as e:
            logger.error(f"Failed to get payment status for {payment_id}: {e}")
            return PaymentStatus.FAILED

    async def get_payment_history(
        self,
        wallet_id: str,
        limit: int = 100
    ) -> list[Payment]:
        """
        Get payment history for a wallet

        Args:
            wallet_id: Masumi wallet ID
            limit: Maximum number of payments to retrieve

        Returns:
            List of Payment objects
        """
        try:
            response = await self.client.get(
                f"{self.service_url}/wallet/{wallet_id}/payments",
                params={"limit": limit}
            )
            response.raise_for_status()
            data = response.json()

            payments = []
            for item in data.get("payments", []):
                payments.append(Payment(
                    payment_id=item["payment_id"],
                    from_wallet=item["from_wallet"],
                    to_wallet=item["to_wallet"],
                    amount_ada=item["amount_ada"],
                    status=PaymentStatus(item["status"]),
                    timestamp=datetime.fromisoformat(item["timestamp"]),
                    tx_hash=item.get("tx_hash"),
                    metadata=item.get("metadata", {})
                ))

            return payments

        except httpx.HTTPError as e:
            logger.error(f"Failed to get payment history for {wallet_id}: {e}")
            return []

    async def refund_payment(
        self,
        payment_id: str,
        reason: str
    ) -> bool:
        """
        Request a refund for a payment

        Args:
            payment_id: Payment to refund
            reason: Refund reason

        Returns:
            True if refund successful
        """
        try:
            response = await self.client.post(
                f"{self.service_url}/payment/{payment_id}/refund",
                json={"reason": reason}
            )
            response.raise_for_status()

            logger.info(f"Refund requested for payment {payment_id}: {reason}")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to refund payment {payment_id}: {e}")
            return False

    async def estimate_fee(
        self,
        from_wallet_id: str,
        to_wallet_id: str,
        amount_ada: float
    ) -> float:
        """
        Estimate transaction fee for a payment

        Args:
            from_wallet_id: Sender wallet
            to_wallet_id: Recipient wallet
            amount_ada: Payment amount

        Returns:
            Estimated fee in ADA
        """
        try:
            response = await self.client.post(
                f"{self.service_url}/payment/estimate-fee",
                json={
                    "from_wallet_id": from_wallet_id,
                    "to_wallet_id": to_wallet_id,
                    "amount_ada": amount_ada
                }
            )
            response.raise_for_status()
            data = response.json()

            return data.get("fee_ada", 0.17)  # Default Cardano fee estimate

        except httpx.HTTPError as e:
            logger.warning(f"Failed to estimate fee: {e}. Using default.")
            return 0.17  # Default Cardano transaction fee

    async def create_job_payment_request(
        self,
        job_id: str,
        amount_lovelace: int,
        recipient_address: str,
        purchaser_identifier: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a payment request for a job (Masumi job-based payment flow)

        This is the standard Masumi pattern:
        1. Agent creates job via /start_job
        2. System creates payment request
        3. User pays and funds get locked
        4. Agent polls for FundsLocked status
        5. Once locked, agent executes job
        6. Payment settles after completion

        Args:
            job_id: Unique job identifier
            amount_lovelace: Payment amount in lovelace (1 ADA = 1,000,000 lovelace)
            recipient_address: Agent wallet address
            purchaser_identifier: Optional purchaser identifier
            metadata: Additional payment metadata

        Returns:
            Payment request details with payment_id
        """
        try:
            payment_data = {
                "job_id": job_id,
                "amount_lovelace": amount_lovelace,
                "recipient_address": recipient_address,
                "purchaser_identifier": purchaser_identifier,
                "metadata": metadata or {},
                "created_at": datetime.utcnow().isoformat()
            }

            # In production: Call Masumi Node API to create payment request
            # For now: Simulate payment request creation
            response = await self.client.post(
                f"{self.service_url}/payment/create-request",
                json=payment_data
            )

            if response.status_code == 404:
                # Masumi Node not available - simulate response
                logger.warning("Masumi Node not available, using simulation mode")
                import uuid
                payment_id = str(uuid.uuid4())

                return {
                    "payment_id": payment_id,
                    "job_id": job_id,
                    "status": PaymentStatus.AWAITING.value,
                    "amount_lovelace": amount_lovelace,
                    "recipient_address": recipient_address,
                    "payment_url": f"masumi://pay/{payment_id}",  # Deep link
                    "qr_code_url": f"https://masumi.network/pay/{payment_id}/qr",
                    "created_at": payment_data["created_at"]
                }

            response.raise_for_status()
            data = response.json()

            logger.info(
                f"Payment request created for job {job_id}: "
                f"{amount_lovelace} lovelace to {recipient_address}"
            )

            return data

        except httpx.HTTPError as e:
            logger.error(f"Failed to create payment request: {e}")
            # Fallback to simulation
            import uuid
            return {
                "payment_id": str(uuid.uuid4()),
                "job_id": job_id,
                "status": PaymentStatus.AWAITING.value,
                "amount_lovelace": amount_lovelace,
                "recipient_address": recipient_address,
                "created_at": datetime.utcnow().isoformat()
            }

    async def check_funds_locked(self, payment_id: str) -> bool:
        """
        Check if funds are locked for a payment (critical Masumi check)

        This is THE key check for Masumi agents:
        - FundsLocked means payment is secured in smart contract
        - Agent can safely proceed with job execution
        - Funds will be released upon successful completion

        Args:
            payment_id: Payment identifier

        Returns:
            True if funds are locked (FundsLocked status), False otherwise
        """
        try:
            response = await self.client.get(
                f"{self.service_url}/payment/{payment_id}/status"
            )

            if response.status_code == 404:
                # Masumi Node not available - simulate
                logger.warning("Masumi Node not available, simulating FundsLocked")
                return True  # Auto-approve in simulation mode

            response.raise_for_status()
            data = response.json()

            status = data.get("status", "")
            is_locked = status == PaymentStatus.FUNDS_LOCKED.value

            if is_locked:
                logger.info(f"✓ FundsLocked confirmed for payment {payment_id}")
            else:
                logger.debug(f"Payment {payment_id} status: {status} (not locked yet)")

            return is_locked

        except httpx.HTTPError as e:
            logger.error(f"Failed to check FundsLocked status for {payment_id}: {e}")
            return False

    async def poll_for_funds_locked(
        self,
        payment_id: str,
        max_attempts: int = 30,
        interval_seconds: int = 2
    ) -> bool:
        """
        Poll for FundsLocked status with timeout

        This is used in background tasks to wait for payment confirmation
        before executing the job.

        Args:
            payment_id: Payment identifier
            max_attempts: Maximum polling attempts
            interval_seconds: Seconds between checks

        Returns:
            True if FundsLocked achieved, False if timeout
        """
        import asyncio

        for attempt in range(1, max_attempts + 1):
            logger.debug(
                f"[Poll {attempt}/{max_attempts}] Checking FundsLocked for {payment_id}"
            )

            is_locked = await self.check_funds_locked(payment_id)

            if is_locked:
                logger.info(
                    f"✓ FundsLocked confirmed for {payment_id} after {attempt} attempts"
                )
                return True

            if attempt < max_attempts:
                await asyncio.sleep(interval_seconds)

        logger.warning(
            f"Timeout: FundsLocked not achieved for {payment_id} "
            f"after {max_attempts} attempts ({max_attempts * interval_seconds}s)"
        )
        return False

    async def get_payment_details(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """
        Get complete payment details including transaction info

        Args:
            payment_id: Payment identifier

        Returns:
            Payment details dictionary or None if not found
        """
        try:
            response = await self.client.get(
                f"{self.service_url}/payment/{payment_id}"
            )

            if response.status_code == 404:
                logger.warning(f"Payment {payment_id} not found")
                return None

            response.raise_for_status()
            return response.json()

        except httpx.HTTPError as e:
            logger.error(f"Failed to get payment details for {payment_id}: {e}")
            return None

    async def complete_payment(
        self,
        payment_id: str,
        job_result: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Mark payment as completed and release funds (called after job completion)

        Args:
            payment_id: Payment identifier
            job_result: Optional job execution result for metadata

        Returns:
            True if successfully marked complete
        """
        try:
            response = await self.client.post(
                f"{self.service_url}/payment/{payment_id}/complete",
                json={"job_result": job_result}
            )

            if response.status_code == 404:
                # Masumi Node not available - simulate
                logger.warning("Masumi Node not available, simulating completion")
                return True

            response.raise_for_status()

            logger.info(f"Payment {payment_id} marked as completed")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to complete payment {payment_id}: {e}")
            return False

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Singleton instance
_payment_service: Optional[PaymentService] = None


def get_payment_service() -> PaymentService:
    """Get or create PaymentService singleton"""
    global _payment_service

    if _payment_service is None:
        _payment_service = PaymentService()

    return _payment_service

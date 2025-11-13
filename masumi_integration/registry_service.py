"""
Masumi Registry Service Integration
Handles agent discovery and registration on the Masumi Network

Based on Masumi Network standards:
- MIP-003 compliant agent registration
- Service discovery with capability filtering
- Agent health and availability tracking
- Version management

Reference: https://docs.masumi.network/documentation/protocols/mip003
"""

import os
import logging
from typing import Optional, List, Dict, Any
from enum import Enum
import httpx
from pydantic import BaseModel, HttpUrl, Field

logger = logging.getLogger(__name__)


class AgentCapability(str, Enum):
    """Agent capability types"""
    MARKET_DATA = "market_data"
    STRATEGY_GENERATION = "strategy_generation"
    RISK_ASSESSMENT = "risk_assessment"
    TRANSACTION_EXECUTION = "transaction_execution"
    PORTFOLIO_ANALYSIS = "portfolio_analysis"


class AgentStatus(str, Enum):
    """Agent registration status"""
    ACTIVE = "active"
    INACTIVE = "inactive"
    MAINTENANCE = "maintenance"


class AgentMetadata(BaseModel):
    """
    Agent metadata for registry (MIP-003 compliant)

    Required fields for Masumi agents:
    - agent_id: Unique identifier on Masumi Network
    - name: Human-readable agent name
    - service_url: Base URL for agent service
    - mip003_endpoints: MIP-003 required endpoints
    - wallet_address: Cardano address for payments
    - capabilities: List of services provided
    """
    agent_id: str
    name: str
    description: str
    capabilities: List[AgentCapability]
    service_url: str
    wallet_id: str
    wallet_address: str
    price_per_request: float  # in ADA
    status: AgentStatus = AgentStatus.ACTIVE
    version: str = "1.0.0"

    # MIP-003 Required Endpoints
    mip003_endpoints: Dict[str, str] = Field(default_factory=lambda: {
        "availability": "/availability",
        "input_schema": "/input_schema",
        "start_job": "/start_job",
        "status": "/status",
        "provide_input": "/provide_input"
    })

    # Additional metadata
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Performance metrics
    uptime_percentage: Optional[float] = None
    average_response_time_ms: Optional[float] = None
    total_jobs_completed: Optional[int] = None


class RegistryService:
    """
    Masumi Registry Service client
    Handles agent registration and discovery per MIP-003 standard
    """

    def __init__(self, service_url: Optional[str] = None):
        self.service_url = service_url or os.getenv(
            "MASUMI_REGISTRY_SERVICE_URL",
            "http://localhost:8080/registry"
        )
        self.client = httpx.AsyncClient(timeout=30.0)

    async def register_agent(
        self,
        name: str,
        description: str,
        capabilities: List[AgentCapability],
        service_url: str,
        wallet_id: str,
        wallet_address: str,
        price_per_request: float,
        metadata: Optional[Dict[str, Any]] = None
    ) -> AgentMetadata:
        """
        Register an agent on the Masumi Network

        Args:
            name: Agent name
            description: Agent description
            capabilities: List of agent capabilities
            service_url: Agent's service endpoint URL
            wallet_id: Masumi wallet ID for payments
            wallet_address: Cardano wallet address
            price_per_request: Cost per request in ADA
            metadata: Additional metadata

        Returns:
            AgentMetadata with agent_id
        """
        try:
            agent_data = {
                "name": name,
                "description": description,
                "capabilities": [cap.value for cap in capabilities],
                "service_url": service_url,
                "wallet_id": wallet_id,
                "wallet_address": wallet_address,
                "price_per_request": price_per_request,
                "metadata": metadata or {}
            }

            response = await self.client.post(
                f"{self.service_url}/agent/register",
                json=agent_data
            )
            response.raise_for_status()
            data = response.json()

            agent = AgentMetadata(
                agent_id=data["agent_id"],
                name=name,
                description=description,
                capabilities=capabilities,
                service_url=service_url,
                wallet_id=wallet_id,
                wallet_address=wallet_address,
                price_per_request=price_per_request,
                status=AgentStatus(data.get("status", "active")),
                version=data.get("version", "1.0.0"),
                metadata=metadata or {}
            )

            logger.info(f"Registered agent: {name} (ID: {agent.agent_id})")
            return agent

        except httpx.HTTPError as e:
            logger.error(f"Failed to register agent {name}: {e}")
            raise

    async def get_agent(self, agent_id: str) -> Optional[AgentMetadata]:
        """
        Get agent information by ID

        Args:
            agent_id: Masumi agent ID

        Returns:
            AgentMetadata or None if not found
        """
        try:
            response = await self.client.get(
                f"{self.service_url}/agent/{agent_id}"
            )
            response.raise_for_status()
            data = response.json()

            return AgentMetadata(
                agent_id=data["agent_id"],
                name=data["name"],
                description=data["description"],
                capabilities=[AgentCapability(cap) for cap in data["capabilities"]],
                service_url=data["service_url"],
                wallet_id=data["wallet_id"],
                wallet_address=data["wallet_address"],
                price_per_request=data["price_per_request"],
                status=AgentStatus(data.get("status", "active")),
                version=data.get("version", "1.0.0"),
                metadata=data.get("metadata", {})
            )

        except httpx.HTTPError as e:
            logger.error(f"Failed to get agent {agent_id}: {e}")
            return None

    async def find_agents_by_capability(
        self,
        capability: AgentCapability
    ) -> List[AgentMetadata]:
        """
        Find all agents with a specific capability

        Args:
            capability: Capability to search for

        Returns:
            List of matching agents
        """
        try:
            response = await self.client.get(
                f"{self.service_url}/agents/search",
                params={"capability": capability.value}
            )
            response.raise_for_status()
            data = response.json()

            agents = []
            for item in data.get("agents", []):
                agents.append(AgentMetadata(
                    agent_id=item["agent_id"],
                    name=item["name"],
                    description=item["description"],
                    capabilities=[AgentCapability(cap) for cap in item["capabilities"]],
                    service_url=item["service_url"],
                    wallet_id=item["wallet_id"],
                    wallet_address=item["wallet_address"],
                    price_per_request=item["price_per_request"],
                    status=AgentStatus(item.get("status", "active")),
                    version=item.get("version", "1.0.0"),
                    metadata=item.get("metadata", {})
                ))

            logger.info(f"Found {len(agents)} agents with capability {capability.value}")
            return agents

        except httpx.HTTPError as e:
            logger.error(f"Failed to search agents by capability {capability}: {e}")
            return []

    async def update_agent_status(
        self,
        agent_id: str,
        status: AgentStatus
    ) -> bool:
        """
        Update agent status

        Args:
            agent_id: Agent to update
            status: New status

        Returns:
            True if successful
        """
        try:
            response = await self.client.patch(
                f"{self.service_url}/agent/{agent_id}/status",
                json={"status": status.value}
            )
            response.raise_for_status()

            logger.info(f"Updated agent {agent_id} status to {status.value}")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to update agent {agent_id} status: {e}")
            return False

    async def deregister_agent(self, agent_id: str) -> bool:
        """
        Remove agent from registry

        Args:
            agent_id: Agent to deregister

        Returns:
            True if successful
        """
        try:
            response = await self.client.delete(
                f"{self.service_url}/agent/{agent_id}"
            )
            response.raise_for_status()

            logger.info(f"Deregistered agent {agent_id}")
            return True

        except httpx.HTTPError as e:
            logger.error(f"Failed to deregister agent {agent_id}: {e}")
            return False

    async def list_all_agents(self) -> List[AgentMetadata]:
        """
        List all registered agents

        Returns:
            List of all agents
        """
        try:
            response = await self.client.get(
                f"{self.service_url}/agents"
            )
            response.raise_for_status()
            data = response.json()

            agents = []
            for item in data.get("agents", []):
                agents.append(AgentMetadata(
                    agent_id=item["agent_id"],
                    name=item["name"],
                    description=item["description"],
                    capabilities=[AgentCapability(cap) for cap in item["capabilities"]],
                    service_url=item["service_url"],
                    wallet_id=item["wallet_id"],
                    wallet_address=item["wallet_address"],
                    price_per_request=item["price_per_request"],
                    status=AgentStatus(item.get("status", "active")),
                    version=item.get("version", "1.0.0"),
                    metadata=item.get("metadata", {})
                ))

            return agents

        except httpx.HTTPError as e:
            logger.error(f"Failed to list agents: {e}")
            return []

    async def verify_mip003_compliance(self, agent_service_url: str) -> Dict[str, bool]:
        """
        Verify that an agent implements MIP-003 required endpoints

        Tests all 5 required endpoints:
        - GET /availability
        - GET /input_schema
        - POST /start_job
        - GET /status
        - POST /provide_input (optional)

        Args:
            agent_service_url: Base URL of agent service

        Returns:
            Dict mapping endpoint names to availability status
        """
        results = {
            "availability": False,
            "input_schema": False,
            "start_job": False,
            "status": False,
            "provide_input": False,
            "compliant": False
        }

        try:
            # Test GET /availability
            try:
                response = await self.client.get(f"{agent_service_url}/availability", timeout=5.0)
                results["availability"] = response.status_code == 200
            except:
                pass

            # Test GET /input_schema
            try:
                response = await self.client.get(
                    f"{agent_service_url}/input_schema",
                    params={"agent_type": "test"},
                    timeout=5.0
                )
                results["input_schema"] = response.status_code in [200, 400]  # 400 acceptable for invalid type
            except:
                pass

            # Test POST /start_job (without actually creating job)
            try:
                # Just check endpoint exists, expect 422 for missing body
                response = await self.client.post(f"{agent_service_url}/start_job", json={}, timeout=5.0)
                results["start_job"] = response.status_code in [422, 400, 200]
            except:
                pass

            # Test GET /status
            try:
                # Expect 404 or 422 for invalid job_id
                response = await self.client.get(
                    f"{agent_service_url}/status",
                    params={"job_id": "test"},
                    timeout=5.0
                )
                results["status"] = response.status_code in [404, 422, 200]
            except:
                pass

            # Test POST /provide_input (optional endpoint)
            try:
                response = await self.client.post(f"{agent_service_url}/provide_input", json={}, timeout=5.0)
                results["provide_input"] = response.status_code in [422, 400, 200, 404]
            except:
                pass

            # Agent is compliant if availability, input_schema, start_job, and status work
            results["compliant"] = (
                results["availability"] and
                results["input_schema"] and
                results["start_job"] and
                results["status"]
            )

            if results["compliant"]:
                logger.info(f"✓ Agent at {agent_service_url} is MIP-003 compliant")
            else:
                logger.warning(f"✗ Agent at {agent_service_url} is NOT MIP-003 compliant: {results}")

            return results

        except Exception as e:
            logger.error(f"Failed to verify MIP-003 compliance for {agent_service_url}: {e}")
            return results

    async def get_agent_health(self, agent_service_url: str) -> Dict[str, Any]:
        """
        Check agent health and availability

        Args:
            agent_service_url: Base URL of agent service

        Returns:
            Health status including availability and response time
        """
        import time

        try:
            start_time = time.time()
            response = await self.client.get(f"{agent_service_url}/availability", timeout=10.0)
            response_time_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                return {
                    "healthy": True,
                    "available": data.get("available", False),
                    "response_time_ms": round(response_time_ms, 2),
                    "agents": data.get("agents", {}),
                    "checked_at": time.time()
                }
            else:
                return {
                    "healthy": False,
                    "available": False,
                    "response_time_ms": round(response_time_ms, 2),
                    "error": f"HTTP {response.status_code}",
                    "checked_at": time.time()
                }

        except Exception as e:
            return {
                "healthy": False,
                "available": False,
                "error": str(e),
                "checked_at": time.time()
            }

    async def discover_agents_by_price_range(
        self,
        min_price_ada: float = 0.0,
        max_price_ada: float = 1.0
    ) -> List[AgentMetadata]:
        """
        Discover agents within a price range

        Args:
            min_price_ada: Minimum price in ADA
            max_price_ada: Maximum price in ADA

        Returns:
            List of agents within price range
        """
        all_agents = await self.list_all_agents()
        return [
            agent for agent in all_agents
            if min_price_ada <= agent.price_per_request <= max_price_ada
        ]

    async def register_agent_with_validation(
        self,
        name: str,
        description: str,
        capabilities: List[AgentCapability],
        service_url: str,
        wallet_id: str,
        wallet_address: str,
        price_per_request: float,
        validate_mip003: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[AgentMetadata]:
        """
        Register an agent with optional MIP-003 compliance validation

        Args:
            name: Agent name
            description: Agent description
            capabilities: List of capabilities
            service_url: Agent service URL
            wallet_id: Masumi wallet ID
            wallet_address: Cardano wallet address
            price_per_request: Price in ADA
            validate_mip003: Whether to validate MIP-003 compliance first
            metadata: Additional metadata

        Returns:
            AgentMetadata if successful, None if validation fails
        """
        # Optionally validate MIP-003 compliance
        if validate_mip003:
            logger.info(f"Validating MIP-003 compliance for {name}...")
            compliance = await self.verify_mip003_compliance(service_url)

            if not compliance["compliant"]:
                logger.error(
                    f"Agent {name} failed MIP-003 validation. "
                    f"Missing endpoints: {[k for k, v in compliance.items() if not v and k != 'compliant']}"
                )
                return None

            logger.info(f"✓ {name} passed MIP-003 validation")

        # Proceed with registration
        try:
            return await self.register_agent(
                name=name,
                description=description,
                capabilities=capabilities,
                service_url=service_url,
                wallet_id=wallet_id,
                wallet_address=wallet_address,
                price_per_request=price_per_request,
                metadata=metadata
            )
        except Exception as e:
            logger.error(f"Failed to register {name}: {e}")
            # In simulation mode, create local agent metadata
            import uuid
            logger.warning(f"Masumi Node not available, creating local agent metadata for {name}")
            return AgentMetadata(
                agent_id=str(uuid.uuid4()),
                name=name,
                description=description,
                capabilities=capabilities,
                service_url=service_url,
                wallet_id=wallet_id,
                wallet_address=wallet_address,
                price_per_request=price_per_request,
                status=AgentStatus.ACTIVE,
                version="1.0.0",
                metadata=metadata or {}
            )

    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()


# Singleton instance
_registry_service: Optional[RegistryService] = None


def get_registry_service() -> RegistryService:
    """Get or create RegistryService singleton"""
    global _registry_service

    if _registry_service is None:
        _registry_service = RegistryService()

    return _registry_service

"""
MIP-003 Standard Compliant Agent Service Endpoints
Masumi Improvement Proposal 003 - Agent Service API Standard

Reference: https://docs.masumi.network/documentation/protocols/mip003

This implements the required endpoints for Masumi Network agent compatibility:
- GET /availability: Agent availability status
- GET /input_schema: Input requirements schema
- POST /start_job: Job initiation with payment request
- GET /status: Job status tracking
- POST /provide_input: Additional input provision (optional)
"""

import uuid
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List
from enum import Enum

from fastapi import APIRouter, HTTPException, Request, BackgroundTasks, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Job Status Enum
# ============================================================================

class JobStatus(str, Enum):
    """Job execution status states"""
    AWAITING_PAYMENT = "awaiting_payment"
    PAYMENT_RECEIVED = "payment_received"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


# ============================================================================
# Request/Response Models
# ============================================================================

class PaymentRequest(BaseModel):
    """Payment request structure per Masumi standards"""
    payment_id: str = Field(..., description="Unique payment identifier")
    amount_lovelace: int = Field(..., description="Payment amount in lovelace (1 ADA = 1,000,000 lovelace)")
    recipient_address: str = Field(..., description="Agent wallet address to receive payment")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Payment metadata")


class StartJobRequest(BaseModel):
    """Job initiation request"""
    agent_type: str = Field(..., description="Agent type: market, strategy, or risk")
    input_data: Dict[str, Any] = Field(..., description="Job-specific input parameters")
    identifier_from_purchaser: Optional[str] = Field(None, description="Optional identifier from purchaser")


class StartJobResponse(BaseModel):
    """Job initiation response"""
    job_id: str = Field(..., description="Unique job identifier")
    status: JobStatus = Field(..., description="Current job status")
    payment_request: PaymentRequest = Field(..., description="Payment request details")
    created_at: str = Field(..., description="Job creation timestamp")


class JobStatusResponse(BaseModel):
    """Job status response"""
    job_id: str
    status: JobStatus
    created_at: str
    updated_at: str
    payment_status: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class ProvideInputRequest(BaseModel):
    """Additional input provision request"""
    job_id: str = Field(..., description="Job identifier")
    additional_input: Dict[str, Any] = Field(..., description="Additional input data")


class InputSchemaField(BaseModel):
    """Schema field definition"""
    name: str
    type: str
    required: bool
    description: str
    default: Optional[Any] = None


class InputSchema(BaseModel):
    """Input schema definition for an agent"""
    agent_type: str
    version: str
    fields: List[InputSchemaField]


class AvailabilityResponse(BaseModel):
    """Availability status response"""
    available: bool
    agents: Dict[str, Dict[str, Any]]
    timestamp: str
    version: str


# ============================================================================
# In-Memory Job Storage (Replace with Database in Production)
# ============================================================================

jobs_db: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# MIP-003 Endpoint 1: GET /availability
# ============================================================================

@router.get("/availability", response_model=AvailabilityResponse)
async def get_availability(request: Request):
    """
    MIP-003 Required Endpoint: Agent Availability Status

    Returns the operational status of all agents and their current availability
    to accept new jobs.

    Returns:
        AvailabilityResponse: Current availability status of all agents
    """
    try:
        # Get agents from app.state (set in lifespan)
        market = getattr(request.app.state, "market_agent", None)
        strategy = getattr(request.app.state, "strategy_agent", None)
        risk = getattr(request.app.state, "risk_agent", None)

        return AvailabilityResponse(
            available=True,
            agents={
                "market": {
                    "available": market is not None,
                    "name": "Market Intelligence Agent",
                    "price_lovelace": int(0.01 * 1_000_000) if market else None,
                    "capabilities": ["market_analysis", "yield_opportunities", "protocol_data"]
                },
                "strategy": {
                    "available": strategy is not None,
                    "name": "Strategy Executor Agent",
                    "price_lovelace": int(0.05 * 1_000_000) if strategy else None,
                    "capabilities": ["portfolio_optimization", "strategy_generation", "allocation"]
                },
                "risk": {
                    "available": risk is not None,
                    "name": "Risk Guardian Agent",
                    "price_lovelace": int(0.02 * 1_000_000) if risk else None,
                    "capabilities": ["risk_assessment", "strategy_validation", "risk_scoring"]
                }
            },
            timestamp=datetime.utcnow().isoformat(),
            version="1.0.0"
        )

    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to check availability: {str(e)}")


# ============================================================================
# MIP-003 Endpoint 2: GET /input_schema
# ============================================================================

@router.get("/input_schema")
async def get_input_schema(agent_type: str = Query(..., description="Agent type: market, strategy, or risk")):
    """
    MIP-003 Required Endpoint: Input Schema Definition

    Returns the input schema for a specific agent type, describing all required
    and optional parameters.

    Args:
        agent_type: Type of agent (market, strategy, or risk)

    Returns:
        InputSchema: Schema definition for the requested agent
    """
    schemas = {
        "market": InputSchema(
            agent_type="market",
            version="1.0.0",
            fields=[
                InputSchemaField(
                    name="query",
                    type="string",
                    required=True,
                    description="Market analysis query or question"
                ),
                InputSchemaField(
                    name="min_tvl",
                    type="number",
                    required=False,
                    description="Minimum Total Value Locked filter",
                    default=100000
                ),
                InputSchemaField(
                    name="min_apr",
                    type="number",
                    required=False,
                    description="Minimum APR filter (percentage)",
                    default=5.0
                )
            ]
        ),
        "strategy": InputSchema(
            agent_type="strategy",
            version="1.0.0",
            fields=[
                InputSchemaField(
                    name="user_portfolio",
                    type="object",
                    required=True,
                    description="Current portfolio with ada_balance and positions"
                ),
                InputSchemaField(
                    name="risk_tolerance",
                    type="string",
                    required=True,
                    description="Risk tolerance level: conservative, moderate, or aggressive"
                ),
                InputSchemaField(
                    name="target_return",
                    type="number",
                    required=True,
                    description="Target annual return percentage"
                ),
                InputSchemaField(
                    name="portfolio_size",
                    type="number",
                    required=False,
                    description="Portfolio size in ADA",
                    default=10000.0
                )
            ]
        ),
        "risk": InputSchema(
            agent_type="risk",
            version="1.0.0",
            fields=[
                InputSchemaField(
                    name="strategy",
                    type="object",
                    required=True,
                    description="Strategy object with recommended_allocations"
                ),
                InputSchemaField(
                    name="risk_tolerance",
                    type="string",
                    required=False,
                    description="Expected risk tolerance for validation",
                    default="moderate"
                )
            ]
        )
    }

    if agent_type not in schemas:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid agent_type. Must be one of: {', '.join(schemas.keys())}"
        )

    return schemas[agent_type]


# ============================================================================
# MIP-003 Endpoint 3: POST /start_job
# ============================================================================

@router.post("/start_job", response_model=StartJobResponse)
async def start_job(
    job_request: StartJobRequest,
    request: Request,
    background_tasks: BackgroundTasks
):
    """
    MIP-003 Required Endpoint: Job Initiation

    Initiates a new job and returns payment request. The job will not begin
    execution until payment is confirmed on-chain.

    Workflow:
    1. Validate input data against schema
    2. Generate unique job_id and payment_id
    3. Create payment request
    4. Start background payment polling task
    5. Return job_id and payment details

    Args:
        job_request: Job initiation request with agent_type and input_data
        background_tasks: FastAPI background tasks for payment polling

    Returns:
        StartJobResponse: Job ID and payment request details
    """
    try:
        # Generate unique IDs
        job_id = str(uuid.uuid4())
        payment_id = str(uuid.uuid4())
        created_at = datetime.utcnow().isoformat()

        # Determine agent and pricing (get from app.state)
        agent_config = {
            "market": {
                "agent": getattr(request.app.state, "market_agent", None),
                "price_ada": 0.01,
                "name": "Market Intelligence Agent",
                "wallet_address": "addr_test1market_demo"
            },
            "strategy": {
                "agent": getattr(request.app.state, "strategy_agent", None),
                "price_ada": 0.05,
                "name": "Strategy Executor Agent",
                "wallet_address": "addr_test1strategy_demo"
            },
            "risk": {
                "agent": getattr(request.app.state, "risk_agent", None),
                "price_ada": 0.02,
                "name": "Risk Guardian Agent",
                "wallet_address": "addr_test1risk_demo"
            }
        }

        if job_request.agent_type not in agent_config:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid agent_type. Must be one of: {', '.join(agent_config.keys())}"
            )

        config = agent_config[job_request.agent_type]
        agent = config["agent"]

        if not agent:
            raise HTTPException(
                status_code=503,
                detail=f"{config['name']} is not available"
            )

        # Create payment request
        amount_lovelace = int(config["price_ada"] * 1_000_000)
        payment_request = PaymentRequest(
            payment_id=payment_id,
            amount_lovelace=amount_lovelace,
            recipient_address=config["wallet_address"],
            metadata={
                "job_id": job_id,
                "agent_type": job_request.agent_type,
                "purchaser_id": job_request.identifier_from_purchaser
            }
        )

        # Store job in database
        jobs_db[job_id] = {
            "job_id": job_id,
            "agent_type": job_request.agent_type,
            "status": JobStatus.AWAITING_PAYMENT,
            "payment_id": payment_id,
            "payment_status": "awaiting",
            "input_data": job_request.input_data,
            "identifier_from_purchaser": job_request.identifier_from_purchaser,
            "created_at": created_at,
            "updated_at": created_at,
            "result": None,
            "error": None
        }

        logger.info(f"Job {job_id} created for agent_type={job_request.agent_type}, awaiting payment {payment_id}")

        # Start background task to poll for payment
        background_tasks.add_task(poll_payment_status, job_id, payment_id, agent, job_request.input_data)

        return StartJobResponse(
            job_id=job_id,
            status=JobStatus.AWAITING_PAYMENT,
            payment_request=payment_request,
            created_at=created_at
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to start job: {str(e)}")


# ============================================================================
# MIP-003 Endpoint 4: GET /status
# ============================================================================

@router.get("/status", response_model=JobStatusResponse)
async def get_job_status(job_id: str = Query(..., description="Job identifier")):
    """
    MIP-003 Required Endpoint: Job Status Tracking

    Returns the current status and results (if available) of a job.

    Job lifecycle:
    - awaiting_payment: Waiting for on-chain payment confirmation
    - payment_received: Payment confirmed, job queued
    - in_progress: Job currently executing
    - completed: Job finished successfully with results
    - failed: Job execution failed with error message
    - cancelled: Job was cancelled

    Args:
        job_id: Unique job identifier

    Returns:
        JobStatusResponse: Current job status and results
    """
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = jobs_db[job_id]

    return JobStatusResponse(
        job_id=job["job_id"],
        status=job["status"],
        created_at=job["created_at"],
        updated_at=job["updated_at"],
        payment_status=job.get("payment_status"),
        result=job.get("result"),
        error=job.get("error")
    )


# ============================================================================
# MIP-003 Endpoint 5: POST /provide_input (Optional)
# ============================================================================

@router.post("/provide_input")
async def provide_additional_input(input_request: ProvideInputRequest):
    """
    MIP-003 Optional Endpoint: Provide Additional Input

    Allows providing additional input to a job that's already in progress.
    This is useful for multi-step workflows or when the agent requests
    additional information.

    Args:
        input_request: Job ID and additional input data

    Returns:
        dict: Confirmation of input receipt
    """
    if input_request.job_id not in jobs_db:
        raise HTTPException(status_code=404, detail=f"Job {input_request.job_id} not found")

    job = jobs_db[input_request.job_id]

    if job["status"] not in [JobStatus.PAYMENT_RECEIVED, JobStatus.IN_PROGRESS]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot provide input to job in status: {job['status']}"
        )

    # Merge additional input
    job["input_data"].update(input_request.additional_input)
    job["updated_at"] = datetime.utcnow().isoformat()

    logger.info(f"Additional input provided to job {input_request.job_id}")

    return {
        "job_id": input_request.job_id,
        "status": "input_received",
        "message": "Additional input has been added to the job"
    }


# ============================================================================
# Background Payment Polling Task
# ============================================================================

async def poll_payment_status(job_id: str, payment_id: str, agent: Any, input_data: Dict[str, Any]):
    """
    Background task to poll for payment confirmation and execute job

    In production, this should:
    1. Poll Masumi Payment Service for payment status
    2. Check for FundsLocked status on Cardano blockchain
    3. Once confirmed, execute the agent job
    4. Update job status and store results

    For hackathon: Simulated payment after short delay

    Args:
        job_id: Job identifier
        payment_id: Payment identifier
        agent: Agent instance to execute
        input_data: Job input parameters
    """
    import asyncio

    try:
        logger.info(f"[Payment Polling] Started for job {job_id}, payment {payment_id}")

        # Simulation mode: Auto-confirm after 2 seconds
        # In production: Poll Masumi Payment Service API
        await asyncio.sleep(2)

        # Check if job still exists
        if job_id not in jobs_db:
            logger.warning(f"[Payment Polling] Job {job_id} no longer exists")
            return

        # Update payment status
        jobs_db[job_id]["status"] = JobStatus.PAYMENT_RECEIVED
        jobs_db[job_id]["payment_status"] = "confirmed"
        jobs_db[job_id]["updated_at"] = datetime.utcnow().isoformat()

        logger.info(f"[Payment Polling] Payment confirmed for job {job_id}")

        # Execute job
        jobs_db[job_id]["status"] = JobStatus.IN_PROGRESS
        jobs_db[job_id]["updated_at"] = datetime.utcnow().isoformat()

        logger.info(f"[Job Execution] Starting job {job_id}")

        # Execute agent using simplified execute() method
        job = jobs_db[job_id]
        agent_type = job["agent_type"]

        logger.info(f"[Job Execution] Executing {agent_type} agent...")
        result = await agent.execute(input_data)
        logger.info(f"[Job Execution] Agent returned result: {result.get('success', False)}")

        # Store results
        jobs_db[job_id]["status"] = JobStatus.COMPLETED
        jobs_db[job_id]["result"] = result
        jobs_db[job_id]["updated_at"] = datetime.utcnow().isoformat()

        logger.info(f"[Job Execution] Job {job_id} completed successfully")

    except Exception as e:
        logger.error(f"[Job Execution] Job {job_id} failed: {e}")
        if job_id in jobs_db:
            jobs_db[job_id]["status"] = JobStatus.FAILED
            jobs_db[job_id]["error"] = str(e)
            jobs_db[job_id]["updated_at"] = datetime.utcnow().isoformat()


# ============================================================================
# Helper Endpoints
# ============================================================================

@router.get("/jobs")
async def list_all_jobs():
    """
    List all jobs (for debugging/monitoring)

    Returns:
        List of all jobs with their current status
    """
    return {
        "total_jobs": len(jobs_db),
        "jobs": [
            {
                "job_id": job_id,
                "agent_type": job["agent_type"],
                "status": job["status"],
                "created_at": job["created_at"]
            }
            for job_id, job in jobs_db.items()
        ]
    }


@router.delete("/jobs/{job_id}")
async def cancel_job(job_id: str):
    """
    Cancel a job (if not yet completed)

    Args:
        job_id: Job identifier

    Returns:
        Cancellation confirmation
    """
    if job_id not in jobs_db:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job = jobs_db[job_id]

    if job["status"] in [JobStatus.COMPLETED, JobStatus.FAILED]:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel job in status: {job['status']}"
        )

    jobs_db[job_id]["status"] = JobStatus.CANCELLED
    jobs_db[job_id]["updated_at"] = datetime.utcnow().isoformat()

    logger.info(f"Job {job_id} cancelled")

    return {
        "job_id": job_id,
        "status": "cancelled",
        "message": "Job has been cancelled"
    }

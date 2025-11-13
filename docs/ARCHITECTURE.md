# Architecture Overview - CashPilot AI

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         User Interface                          │
│                    (Web/API/CLI Clients)                        │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ REST API
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FastAPI Server                             │
│                     (api/main.py)                               │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐        │
│  │   Health     │  │    Agents    │  │  Portfolio   │        │
│  │   Routes     │  │    Routes    │  │   Routes     │        │
│  └──────────────┘  └──────────────┘  └──────────────┘        │
└───────────────┬─────────────┬─────────────┬───────────────────┘
                │             │             │
        ┌───────┴─────┐   ┌──┴──────┐   ┌──┴─────────┐
        │             │   │         │   │            │
        ▼             ▼   ▼         ▼   ▼            ▼
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│   Market     │ │  Strategy    │ │    Risk      │
│ Intelligence │ │  Executor    │ │  Guardian    │
│    Agent     │ │    Agent     │ │    Agent     │
│              │ │              │ │              │
│  Price: 0.01 │ │ Price: 0.05  │ │ Price: 0.02  │
│     ADA      │ │     ADA      │ │     ADA      │
└──────┬───────┘ └──────┬───────┘ └──────┬───────┘
       │                │                │
       │   ┌────────────┼────────────┐   │
       │   │            │            │   │
       ▼   ▼            ▼            ▼   ▼
┌─────────────────────────────────────────────────┐
│        Masumi Network Integration               │
│                                                 │
│  ┌───────────────┐  ┌────────────────────┐    │
│  │   Payment     │  │     Registry       │    │
│  │   Service     │  │     Service        │    │
│  │               │  │                    │    │
│  │ Agent-to-     │  │  Agent Discovery   │    │
│  │ Agent Payments│  │  & Registration    │    │
│  └───────────────┘  └────────────────────┘    │
└──────────────────┬──────────────────────────────┘
                   │
                   ▼
         ┌─────────────────────┐
         │   Masumi Node       │
         │  (Port 8080)        │
         │                     │
         │  - Wallet Manager   │
         │  - Tx Batching      │
         │  - Smart Contracts  │
         └──────────┬──────────┘
                    │
                    ▼
         ┌─────────────────────┐
         │  Cardano Blockchain │
         │    (Preprod/Mainnet)│
         │                     │
         │  - Smart Contracts  │
         │  - Payment Records  │
         │  - Agent Registry   │
         └─────────────────────┘
```

## Agent Collaboration Flow

```
┌─────────┐
│  User   │
│ Request │
└────┬────┘
     │ 0.05 ADA
     ▼
┌────────────────────┐
│ Strategy Executor  │◄─────────┐
│      Agent         │          │
└─┬────────────────┬─┘          │
  │                │            │
  │ 0.01 ADA       │ 0.02 ADA   │
  │                │            │
  ▼                ▼            │
┌──────────┐    ┌──────────┐   │
│ Market   │    │   Risk   │   │
│  Intel   │    │ Guardian │   │
│  Agent   │    │  Agent   │   │
└────┬─────┘    └────┬─────┘   │
     │               │          │
     │ Market Data   │ Risk     │
     └───────┬───────┘ Validation
             │          │
             └──────────┘
                  │
             ┌────▼─────┐
             │ Approved │
             │ Strategy │
             └──────────┘
```

## Data Flow

### 1. Market Data Fetching

```
Market Intelligence Agent
        │
        ├─► Blockfrost API (Cardano Blockchain Data)
        │   └─► Address balances, UTXOs, transactions
        │
        ├─► Minswap API (DEX Data)
        │   └─► Pool reserves, TVL, APR, volume
        │
        ├─► SundaeSwap API (DEX Data)
        │   └─► Pool metrics, liquidity, fees
        │
        └─► Liqwid API (Lending Data)
            └─► Supply APR, borrow APR, utilization
```

### 2. Strategy Generation

```
Strategy Executor Agent
        │
        ├─► Request Market Data
        │   └─► Get yield opportunities
        │       └─► Filter by TVL, APR, risk
        │
        ├─► Run Optimization Algorithm
        │   ├─► Calculate optimal allocations
        │   ├─► Consider user risk tolerance
        │   ├─► Maximize risk-adjusted returns
        │   └─► Generate rebalancing transactions
        │
        └─► Request Risk Validation
            └─► Check concentration risk
            └─► Validate protocol safety
            └─► Approve/reject strategy
```

### 3. Payment Processing

```
User Wallet
    │ 0.05 ADA
    ▼
Strategy Agent Wallet
    │
    ├─► 0.01 ADA → Market Agent Wallet
    │   └─► Masumi Payment Service
    │       └─► Cardano Transaction
    │           └─► On-chain Record
    │
    └─► 0.02 ADA → Risk Agent Wallet
        └─► Masumi Payment Service
            └─► Cardano Transaction
                └─► On-chain Record
```

## Component Details

### Agents Layer

Each agent consists of:

1. **Agent Class** (`agent.py`)
   - LangChain agent with Claude 3.5 Sonnet
   - Masumi integration (payments, registry)
   - Business logic and workflows

2. **Tools** (`tools.py` or specialized modules)
   - External API integrations
   - Data processing functions
   - Blockchain operations

3. **Configuration** (`config.json` or environment)
   - Wallet IDs and addresses
   - Pricing information
   - Service URLs

### Masumi Integration Layer

```python
# masumi_integration/
├── payment_service.py     # Agent-to-agent payments
├── registry_service.py    # Agent discovery & registration
└── wallet_manager.py      # Wallet operations
```

**Key Features:**
- Payment creation and tracking
- Agent registration (MIP-003 compliant)
- Wallet balance management
- Transaction history

### Cardano Integration Layer

```python
# cardano/
├── blockfrost_client.py   # Blockchain queries
├── defi_protocols.py      # DeFi protocol APIs
└── transaction_builder.py # Transaction construction
```

**Capabilities:**
- Address and UTXO queries
- Transaction submission
- DEX pool data fetching
- Lending market analysis

### API Layer

```python
# api/
├── main.py               # FastAPI app & lifecycle
└── routes/
    ├── health.py         # Health checks
    ├── agents.py         # Agent endpoints
    └── portfolio.py      # Portfolio workflows
```

**Endpoints:**
- `/health` - System health
- `/agents/market/query` - Market data
- `/agents/strategy/generate` - Strategy generation
- `/agents/risk/assess` - Risk assessment
- `/portfolio/optimize` - End-to-end optimization

## Database Schema (Planned)

```sql
-- Agents
CREATE TABLE agents (
    agent_id VARCHAR PRIMARY KEY,
    name VARCHAR,
    wallet_id VARCHAR,
    wallet_address VARCHAR,
    price_per_request DECIMAL,
    status VARCHAR,
    created_at TIMESTAMP
);

-- Strategies
CREATE TABLE strategies (
    strategy_id VARCHAR PRIMARY KEY,
    user_address VARCHAR,
    risk_tolerance VARCHAR,
    target_return DECIMAL,
    allocations JSONB,
    risk_score DECIMAL,
    approved BOOLEAN,
    created_at TIMESTAMP
);

-- Payments
CREATE TABLE payments (
    payment_id VARCHAR PRIMARY KEY,
    from_wallet VARCHAR,
    to_wallet VARCHAR,
    amount_ada DECIMAL,
    description TEXT,
    status VARCHAR,
    tx_hash VARCHAR,
    created_at TIMESTAMP
);

-- User Portfolios
CREATE TABLE portfolios (
    portfolio_id VARCHAR PRIMARY KEY,
    user_address VARCHAR,
    positions JSONB,
    total_value_ada DECIMAL,
    last_rebalanced TIMESTAMP
);
```

## Security Considerations

### 1. API Security
- Rate limiting per wallet
- Input validation
- SQL injection prevention
- XSS protection

### 2. Wallet Security
- Private keys never stored in code
- Environment variable configuration
- Masumi wallet isolation

### 3. Payment Security
- Escrow mechanisms
- Dispute resolution
- Refund capabilities
- Transaction verification

### 4. Smart Contract Security
- Masumi audited contracts
- On-chain verification
- Immutable payment records

## Scalability

### Horizontal Scaling

```
Load Balancer
    │
    ├─► API Server 1 ──► Agent Pool 1
    ├─► API Server 2 ──► Agent Pool 2
    ├─► API Server 3 ──► Agent Pool 3
    └─► API Server N ──► Agent Pool N
         │
         └─► Shared Database (PostgreSQL)
         └─► Shared Cache (Redis)
```

### Optimization Strategies

1. **Caching**
   - Redis for market data (TTL: 60s)
   - Protocol data caching
   - Agent response caching

2. **Database**
   - Connection pooling
   - Read replicas
   - Query optimization

3. **API**
   - Async operations
   - Request queuing
   - Background jobs

4. **Agents**
   - Stateless design
   - Multiple instances
   - Load balancing

## Monitoring & Observability

### Metrics to Track

1. **Agent Performance**
   - Response times
   - Success/failure rates
   - Revenue per agent

2. **Payment Metrics**
   - Total payments processed
   - Average payment amount
   - Payment success rate

3. **System Health**
   - API latency
   - Database connections
   - Cache hit rate

4. **Business Metrics**
   - Active users
   - Strategies generated
   - Total ADA managed

## Deployment Architecture

### Development
```
Local Machine
├── Python Virtual Env
├── Masumi Node (Docker)
├── PostgreSQL (Docker)
└── Redis (Docker)
```

### Production (Recommended)
```
Cloud Provider (AWS/GCP/Azure)
├── Container Service (ECS/GKE/AKS)
│   ├── API Pods (auto-scaling)
│   └── Agent Services
├── Managed Database (RDS/Cloud SQL)
├── Managed Cache (ElastiCache/Memorystore)
├── Load Balancer
└── Masumi Node (dedicated instance)
```

## Technology Stack Summary

| Layer | Technology | Purpose |
|-------|-----------|---------|
| AI/LLM | Claude 3.5 Sonnet | Agent intelligence |
| Agent Framework | LangChain | Agent orchestration |
| Backend | FastAPI | REST API |
| Database | PostgreSQL | Data persistence |
| Cache | Redis | Performance |
| Blockchain | Cardano | Payments & registry |
| Agent Platform | Masumi Network | Agent infrastructure |
| Deployment | Docker | Containerization |
| Language | Python 3.11 | Primary language |

## Future Architecture Enhancements

1. **WebSocket Support** for real-time updates
2. **GraphQL API** for flexible queries
3. **Event Sourcing** for audit trails
4. **Message Queue** (RabbitMQ) for async tasks
5. **Microservices** splitting for scalability
6. **Multi-region deployment** for global access
7. **CDN integration** for frontend
8. **Machine Learning pipeline** for strategy optimization

---

This architecture is designed to be:
- **Scalable:** Handle growing user base
- **Reliable:** Fault-tolerant and resilient
- **Secure:** Multiple layers of security
- **Maintainable:** Clear separation of concerns
- **Extensible:** Easy to add new agents and features

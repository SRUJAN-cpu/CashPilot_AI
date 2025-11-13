# CashPilot AI - Masumi DeFi Multi-Agent System 🚀

> AI-powered DeFi portfolio optimization on Cardano via Masumi Network

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Masumi Network](https://img.shields.io/badge/Masumi-Network-blue)](https://masumi.network)
[![Cardano](https://img.shields.io/badge/Cardano-Blockchain-blue)](https://cardano.org)

## Overview

**CashPilot AI** is a hackathon project demonstrating multi-agent AI collaboration on the Masumi Network for automated DeFi portfolio management on Cardano. Three specialized AI agents work together, communicating and transacting via Masumi's payment infrastructure to provide comprehensive yield optimization.

### The Problem

Managing DeFi portfolios across multiple Cardano protocols (Minswap, SundaeSwap, Liqwid, etc.) requires:
- Constant monitoring of yield rates and opportunities
- Complex portfolio optimization calculations
- Risk assessment and validation
- Transaction execution across multiple protocols

### The Solution

Three AI agents collaborate autonomously:

1. **Market Intelligence Agent** ($0.01/query)
   - Fetches real-time yield data from Cardano DEXs
   - Analyzes protocol metrics (TVL, APR, volume)
   - Identifies best yield opportunities

2. **Strategy Executor Agent** ($0.05/execution)
   - Generates optimal portfolio allocations
   - Pays Market Agent for data
   - Pays Risk Agent for validation
   - Executes approved strategies

3. **Risk Guardian Agent** ($0.02/check)
   - Validates strategy safety
   - Monitors portfolio health
   - Enforces risk limits

## Architecture

```
User Request
    ↓
Strategy Executor Agent ($0.05)
    ├─→ Market Intelligence Agent ($0.01) → Market Data
    ├─→ Risk Guardian Agent ($0.02) → Risk Validation
    └─→ Approved Strategy → Cardano Blockchain
```

### Technology Stack

- **AI Framework**: LangChain + CrewAI with Groq (Llama 3.1)
- **LLM**: Groq API (100% FREE - no credit card needed!)
- **Blockchain**: Cardano (Preprod Testnet)
- **Payments**: Masumi Network (on-chain agent-to-agent)
- **Data**: Blockfrost API, DEX APIs
- **Backend**: FastAPI + Python 3.11
- **Database**: PostgreSQL + Redis
- **Deployment**: Docker Compose

## Features

### Multi-Agent Collaboration
- Agents discover each other via Masumi Registry
- Automated payments for services (agent-to-agent)
- Transparent payment trails on Cardano blockchain

### DeFi Integration
- Minswap DEX integration
- SundaeSwap DEX integration
- Liqwid lending protocol support
- Real-time yield data and TVL metrics

### Portfolio Optimization
- Risk-adjusted return maximization
- Multiple optimization algorithms
- Customizable risk profiles (conservative/moderate/aggressive)
- Transaction fee optimization

### Risk Management
- Protocol safety scoring
- Concentration risk analysis
- Liquidity risk monitoring
- Stop-loss and safety checks

## Getting Started

### Prerequisites

- Python 3.11+
- Docker & Docker Compose
- Masumi Node (see [Masumi Docs](https://docs.masumi.network))
- Groq API key (FREE at https://console.groq.com)
- Blockfrost API key (FREE - Cardano Preprod)

### Installation

1. **Clone the repository**
```bash
git clone https://github.com/yourusername/CashPilot_AI.git
cd CashPilot_AI
```

2. **Set up environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys and wallet IDs
```

3. **Install dependencies**
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install packages
pip install -r requirements.txt
```

4. **Set up Masumi Node**
```bash
# Follow Masumi Network documentation
# Create wallets for each agent
# Fund wallets with test-ADA
```

5. **Start services**
```bash
# Using Docker
docker-compose up -d

# Or run locally
uvicorn api.main:app --reload
```

### Configuration

Edit `.env` file:

```bash
# Masumi Network
MASUMI_NODE_URL=http://localhost:8080
MASUMI_PAYMENT_SERVICE_URL=http://localhost:8080/payment
MASUMI_REGISTRY_SERVICE_URL=http://localhost:8080/registry

# Agent Wallets (create via Masumi Node)
MARKET_AGENT_WALLET_ID=your_market_wallet_id
MARKET_AGENT_WALLET_ADDRESS=addr_test1...
STRATEGY_AGENT_WALLET_ID=your_strategy_wallet_id
STRATEGY_AGENT_WALLET_ADDRESS=addr_test1...
RISK_AGENT_WALLET_ID=your_risk_wallet_id
RISK_AGENT_WALLET_ADDRESS=addr_test1...

# Cardano
CARDANO_NETWORK=preprod
BLOCKFROST_PROJECT_ID=your_blockfrost_project_id

# AI (Get FREE at https://console.groq.com)
GROQ_API_KEY=your_groq_api_key
```

## Usage

### API Endpoints

**Base URL**: `http://localhost:8000`

#### 1. Get Yield Opportunities
```bash
GET /agents/market/opportunities?min_tvl=100000&min_apr=5.0
```

#### 2. Generate Portfolio Strategy
```bash
POST /agents/strategy/generate
Content-Type: application/json

{
  "user_portfolio": {
    "ada_balance": 10000,
    "positions": []
  },
  "risk_tolerance": "moderate",
  "target_return": 12.0,
  "requester_wallet_id": "user_wallet_123"
}
```

#### 3. Assess Risk
```bash
POST /agents/risk/assess
Content-Type: application/json

{
  "strategy": {
    "strategy_id": "uuid",
    "recommended_allocations": [...]
  },
  "requester_wallet_id": "strategy_agent_wallet"
}
```

#### 4. Complete Portfolio Optimization
```bash
POST /portfolio/optimize
Content-Type: application/json

{
  "user_address": "addr_test1...",
  "current_portfolio": {
    "ada_balance": 10000,
    "positions": []
  },
  "risk_tolerance": "moderate",
  "target_return": 12.0,
  "user_wallet_id": "user_wallet_123"
}
```

### Example Response

```json
{
  "success": true,
  "strategy": {
    "strategy_id": "abc-123",
    "recommended_allocations": [
      {
        "protocol": "minswap",
        "pool": "ADA/DJED",
        "allocation_percent": 40,
        "expected_apr": 12.5,
        "risk_score": 25
      },
      {
        "protocol": "sundaeswap",
        "pool": "ADA/MIN",
        "allocation_percent": 30,
        "expected_apr": 15.8,
        "risk_score": 35
      },
      {
        "protocol": "liqwid",
        "asset": "ADA",
        "allocation_percent": 30,
        "expected_apr": 8.2,
        "risk_score": 20
      }
    ],
    "expected_portfolio_apr": 12.5,
    "expected_portfolio_risk": 27.5
  },
  "risk_validation": {
    "approved": true,
    "overall_risk_score": 27.5
  },
  "total_cost_ada": 0.05,
  "agent_payments": {
    "strategy_executor": 0.05,
    "market_intelligence": 0.01,
    "risk_guardian": 0.02
  }
}
```

## Project Structure

```
CashPilot_AI/
├── agents/                     # AI Agent implementations
│   ├── market_intelligence/    # Market data agent
│   │   ├── agent.py
│   │   └── tools.py
│   ├── strategy_executor/      # Strategy generation agent
│   │   ├── agent.py
│   │   └── optimizer.py
│   └── risk_guardian/          # Risk assessment agent
│       ├── agent.py
│       └── risk_models.py
├── masumi_integration/         # Masumi Network integration
│   ├── payment_service.py
│   ├── registry_service.py
│   └── wallet_manager.py
├── cardano/                    # Cardano blockchain integration
│   ├── blockfrost_client.py
│   ├── defi_protocols.py
│   └── transaction_builder.py
├── api/                        # FastAPI server
│   ├── main.py
│   └── routes/
│       ├── health.py
│       ├── agents.py
│       └── portfolio.py
├── docker/                     # Docker configuration
│   └── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Monetization Model

### Agent Revenue Streams

| Agent | Price | Revenue | Costs | Net Profit |
|-------|-------|---------|-------|------------|
| Market Intelligence | $0.01/query | $0.01 | $0 | **$0.01** |
| Strategy Executor | $0.05/execution | $0.05 | $0.03 | **$0.02** |
| Risk Guardian | $0.02/check | $0.02 | $0 | **$0.02** |

### Agent-to-Agent Payments

Every strategy execution triggers:
1. User → Strategy Agent: **0.05 ADA**
2. Strategy Agent → Market Agent: **0.01 ADA** (data)
3. Strategy Agent → Risk Agent: **0.02 ADA** (validation)

All payments recorded on Cardano blockchain via Masumi smart contracts.

## Development

### Running Tests

```bash
pytest tests/ -v --cov=.
```

### Local Development

```bash
# Start services individually
python -m uvicorn api.main:app --reload --port 8000
```

### Adding New Agents

1. Create agent directory in `agents/`
2. Implement agent class with Masumi integration
3. Register in Masumi Registry
4. Add routes in `api/routes/`

## Hackathon Submission

### Demo Video
[Link to demo video]

### Live Demo
[Link to deployed instance]

### Presentation
[Link to slides]

## Roadmap

### Phase 1 (Hackathon - ✅ Complete)
- [x] Multi-agent system architecture
- [x] Masumi Network integration
- [x] Basic DeFi protocol support
- [x] Agent-to-agent payments
- [x] REST API

### Phase 2 (Post-Hackathon)
- [ ] Frontend dashboard
- [ ] More DeFi protocols (Indigo, WingRiders, MuesliSwap)
- [ ] Advanced optimization algorithms
- [ ] Real transaction execution on mainnet
- [ ] Historical performance tracking
- [ ] WebSocket real-time updates

### Phase 3 (Production)
- [ ] Multi-user support
- [ ] Agent reputation system
- [ ] Dispute resolution
- [ ] Mobile app
- [ ] Additional agent types (tax reporting, compliance)

## Security Considerations

- Never commit private keys or sensitive credentials
- Use test-ADA only on preprod network
- Validate all transactions before signing
- Implement rate limiting for agent requests
- Audit smart contracts before mainnet deployment

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

## License

MIT License - see [LICENSE](LICENSE) file

## Acknowledgments

- [Masumi Network](https://masumi.network) for agent infrastructure
- [Cardano Foundation](https://cardano.org) for blockchain platform
- [Anthropic](https://anthropic.com) for Claude AI
- [LangChain](https://langchain.com) for agent framework

## Contact

- Project Link: [https://github.com/yourusername/CashPilot_AI](https://github.com/yourusername/CashPilot_AI)
- Hackathon: Masumi AI Agents on Cardano
- Team: [Your Name/Team Name]

---

Built with ❤️ for the Masumi AI Agents Hackathon

# Setup Guide - CashPilot AI

Complete setup instructions for running CashPilot AI locally or in production.

## Prerequisites Checklist

- [ ] Python 3.11 or higher installed
- [ ] Docker and Docker Compose installed
- [ ] Git installed
- [ ] Anthropic API key ([Get one here](https://console.anthropic.com/))
- [ ] Blockfrost API key for Cardano Preprod ([Get one here](https://blockfrost.io/))
- [ ] Masumi Node installed and running

## Step-by-Step Setup

### 1. Clone and Setup Environment

```bash
# Clone repository
git clone https://github.com/yourusername/CashPilot_AI.git
cd CashPilot_AI

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Linux/Mac:
source venv/bin/activate
# On Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Install and Configure Masumi Node

#### Option A: Docker (Recommended)

```bash
# Pull Masumi Node image
docker pull masumi/node:latest

# Create Masumi data directory
mkdir -p masumi-node-data

# Run Masumi Node
docker run -d \
  --name masumi-node \
  -p 8080:8080 \
  -v $(pwd)/masumi-node-data:/data \
  -e MASUMI_NETWORK=preprod \
  masumi/node:latest
```

#### Option B: Native Installation

Follow the official Masumi documentation:
https://docs.masumi.network/documentation/getting-started

### 3. Create Agent Wallets

Each agent needs its own Masumi wallet:

```bash
# Start Masumi Node
# Access Masumi CLI or API

# Create Market Intelligence Agent wallet
curl -X POST http://localhost:8080/payment/wallet/create \
  -H "Content-Type: application/json" \
  -d '{"name": "market_intelligence"}'

# Save the wallet_id and address returned

# Create Strategy Executor Agent wallet
curl -X POST http://localhost:8080/payment/wallet/create \
  -H "Content-Type: application/json" \
  -d '{"name": "strategy_executor"}'

# Create Risk Guardian Agent wallet
curl -X POST http://localhost:8080/payment/wallet/create \
  -H "Content-Type: application/json" \
  -d '{"name": "risk_guardian"}'
```

### 4. Fund Wallets with Test-ADA

Use the Cardano Preprod faucet:

```bash
# Visit: https://faucet.preprod.world.dev.cardano.org/

# Request test-ADA for each agent wallet address
# Each wallet needs at least 100 test-ADA for operations
```

Or use curl:

```bash
curl -X POST https://faucet.preprod.world.dev.cardano.org/send-money \
  -H "Content-Type: application/json" \
  -d '{"address": "YOUR_WALLET_ADDRESS"}'
```

### 5. Get API Keys

#### Blockfrost API Key

1. Go to https://blockfrost.io/
2. Sign up for free account
3. Create new project for "Cardano Preprod"
4. Copy the project ID

#### Anthropic API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Go to API Keys section
4. Create new key
5. Copy the key

### 6. Configure Environment Variables

```bash
# Copy example environment file
cp .env.example .env

# Edit .env file with your values
nano .env  # or use your preferred editor
```

Example `.env`:

```bash
# Masumi Network
MASUMI_NODE_URL=http://localhost:8080
MASUMI_PAYMENT_SERVICE_URL=http://localhost:8080/payment
MASUMI_REGISTRY_SERVICE_URL=http://localhost:8080/registry
MASUMI_NETWORK=preprod

# Agent Wallets (from step 3)
MARKET_AGENT_WALLET_ID=wallet_1a2b3c4d
MARKET_AGENT_WALLET_ADDRESS=addr_test1qz...
STRATEGY_AGENT_WALLET_ID=wallet_5e6f7g8h
STRATEGY_AGENT_WALLET_ADDRESS=addr_test1qp...
RISK_AGENT_WALLET_ID=wallet_9i0j1k2l
RISK_AGENT_WALLET_ADDRESS=addr_test1qx...

# Cardano Configuration
CARDANO_NETWORK=preprod
BLOCKFROST_PROJECT_ID=preprodXYZ123...  # Your Blockfrost key
BLOCKFROST_API_URL=https://cardano-preprod.blockfrost.io/api/v0

# AI/LLM Configuration
ANTHROPIC_API_KEY=sk-ant-...  # Your Anthropic key

# Database Configuration
DATABASE_URL=postgresql://cashpilot_user:password@localhost:5432/cashpilot
REDIS_URL=redis://localhost:6379/0

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=1
DEBUG=True

# Agent Pricing (in ADA)
MARKET_AGENT_PRICE=0.01
STRATEGY_AGENT_PRICE=0.05
RISK_AGENT_PRICE=0.02
```

### 7. Start Services

#### Option A: Using Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Check logs
docker-compose logs -f api

# Check health
curl http://localhost:8000/health
```

#### Option B: Manual Start

```bash
# Terminal 1: Start PostgreSQL
docker run -d \
  --name postgres \
  -e POSTGRES_DB=cashpilot \
  -e POSTGRES_USER=cashpilot_user \
  -e POSTGRES_PASSWORD=password \
  -p 5432:5432 \
  postgres:15-alpine

# Terminal 2: Start Redis
docker run -d \
  --name redis \
  -p 6379:6379 \
  redis:7-alpine

# Terminal 3: Start API
python -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

### 8. Verify Installation

```bash
# Check API health
curl http://localhost:8000/health

# Check agents status
curl http://localhost:8000/health/agents

# Get agents info
curl http://localhost:8000/agents/info
```

Expected response:
```json
{
  "status": "healthy",
  "agents": {
    "market_intelligence": {
      "status": "active",
      "agent_id": "agent_abc123",
      "wallet_id": "wallet_1a2b3c4d"
    },
    ...
  }
}
```

### 9. Test the System

```bash
# Test market data query
curl -X POST http://localhost:8000/agents/market/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the top yield opportunities on Minswap?",
    "requester_wallet_id": null
  }'

# Test portfolio optimization
curl -X POST http://localhost:8000/portfolio/optimize \
  -H "Content-Type: application/json" \
  -d '{
    "user_address": "addr_test1...",
    "current_portfolio": {
      "ada_balance": 10000,
      "positions": []
    },
    "risk_tolerance": "moderate",
    "target_return": 12.0,
    "user_wallet_id": "user_wallet_123"
  }'
```

## Troubleshooting

### Agents not registering on Masumi

**Issue**: Agents fail to register with "Connection refused" error

**Solution**:
1. Verify Masumi Node is running: `docker ps | grep masumi`
2. Check Masumi Node logs: `docker logs masumi-node`
3. Verify MASUMI_NODE_URL in .env matches running instance
4. Ensure wallets are created and funded

### Blockfrost API errors

**Issue**: "Invalid project ID" or "401 Unauthorized"

**Solution**:
1. Verify Blockfrost project ID is correct
2. Ensure you're using Preprod project, not mainnet
3. Check API key hasn't expired
4. Verify BLOCKFROST_API_URL uses preprod endpoint

### Agent payment failures

**Issue**: "Insufficient funds" or payment timeouts

**Solution**:
1. Check wallet balances: `curl http://localhost:8080/payment/wallet/{wallet_id}/balance`
2. Request more test-ADA from faucet
3. Wait for transactions to confirm (may take 20-60 seconds)
4. Check Cardano network status

### Docker connection issues

**Issue**: Services can't connect to each other

**Solution**:
1. Ensure all services are on same Docker network
2. Use service names (not localhost) in docker-compose
3. Check docker-compose logs for connection errors
4. Restart services: `docker-compose restart`

### Import errors in Python

**Issue**: `ModuleNotFoundError` or import errors

**Solution**:
1. Verify virtual environment is activated
2. Reinstall dependencies: `pip install -r requirements.txt`
3. Check Python version: `python --version` (should be 3.11+)
4. Try: `pip install --upgrade pip setuptools`

## Advanced Configuration

### Production Deployment

For production deployment:

1. Use strong database passwords
2. Enable SSL/TLS for API endpoints
3. Set up proper logging and monitoring
4. Use mainnet instead of preprod
5. Implement rate limiting
6. Set up backup strategies
7. Use environment-specific .env files

### Scaling with Multiple Workers

```bash
# In .env
API_WORKERS=4

# Or via command line
uvicorn api.main:app --workers 4 --host 0.0.0.0 --port 8000
```

### Custom Agent Pricing

Adjust agent prices in .env:

```bash
MARKET_AGENT_PRICE=0.02  # Increase price
STRATEGY_AGENT_PRICE=0.10
RISK_AGENT_PRICE=0.05
```

## Next Steps

- Read the [API Documentation](API.md)
- Check out [Usage Examples](EXAMPLES.md)
- Review [Architecture Overview](ARCHITECTURE.md)
- Join the community on Discord

## Support

If you encounter issues not covered here:

1. Check GitHub Issues
2. Review Masumi Network documentation
3. Ask in Discord community
4. Create a new GitHub issue with logs

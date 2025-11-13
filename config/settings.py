"""
Centralized Configuration for CashPilot AI
Uses Pydantic for type-safe configuration management

All settings loaded from environment variables with validation
"""

import os
from typing import Optional, Literal
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class MasumiSettings(BaseModel):
    """Masumi Network configuration"""
    node_url: str = Field(
        default="http://localhost:8080",
        description="Masumi Node base URL"
    )
    payment_service_url: str = Field(
        default="http://localhost:8080/payment",
        description="Masumi Payment Service URL"
    )
    registry_service_url: str = Field(
        default="http://localhost:8080/registry",
        description="Masumi Registry Service URL"
    )
    network: Literal["preprod", "mainnet"] = Field(
        default="preprod",
        description="Masumi network environment"
    )
    operational_mode: Literal["production", "simulation", "api"] = Field(
        default="simulation",
        description="Operational mode"
    )
    enable_mip003_validation: bool = Field(
        default=True,
        description="Validate MIP-003 compliance on agent registration"
    )
    auto_register_agents: bool = Field(
        default=True,
        description="Automatically register agents on startup"
    )


class AgentWalletSettings(BaseModel):
    """Agent wallet configuration"""
    # Market Intelligence Agent
    market_wallet_id: str = Field(
        default="market_wallet_1",
        description="Market agent wallet ID"
    )
    market_wallet_address: str = Field(
        default="addr_test1qz...",
        description="Market agent Cardano address"
    )

    # Strategy Executor Agent
    strategy_wallet_id: str = Field(
        default="strategy_wallet_1",
        description="Strategy agent wallet ID"
    )
    strategy_wallet_address: str = Field(
        default="addr_test1qz...",
        description="Strategy agent Cardano address"
    )

    # Risk Guardian Agent
    risk_wallet_id: str = Field(
        default="risk_wallet_1",
        description="Risk agent wallet ID"
    )
    risk_wallet_address: str = Field(
        default="addr_test1qz...",
        description="Risk agent Cardano address"
    )


class CardanoSettings(BaseModel):
    """Cardano blockchain configuration"""
    network: Literal["preprod", "mainnet"] = Field(
        default="preprod",
        description="Cardano network"
    )
    blockfrost_project_id: str = Field(
        ...,
        description="Blockfrost API project ID"
    )
    blockfrost_api_url: str = Field(
        default="https://cardano-preprod.blockfrost.io/api/v0",
        description="Blockfrost API base URL"
    )

    @validator("blockfrost_api_url", always=True)
    def set_blockfrost_url(cls, v, values):
        """Auto-set Blockfrost URL based on network"""
        network = values.get("network", "preprod")
        if network == "mainnet":
            return "https://cardano-mainnet.blockfrost.io/api/v0"
        return "https://cardano-preprod.blockfrost.io/api/v0"


class LLMSettings(BaseModel):
    """AI/LLM configuration"""
    groq_api_key: str = Field(
        ...,
        description="Groq API key"
    )
    model: str = Field(
        default="llama-3.1-70b-versatile",
        description="LLM model to use"
    )
    temperature: float = Field(
        default=0.1,
        description="LLM temperature (0.0 to 1.0)"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        description="Maximum tokens per request"
    )

    # Alternative LLM providers (optional)
    openai_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None


class AgentPricingSettings(BaseModel):
    """Agent pricing configuration (in ADA)"""
    market_agent_price: float = Field(
        default=0.01,
        description="Market Intelligence Agent price per query"
    )
    strategy_agent_price: float = Field(
        default=0.05,
        description="Strategy Executor Agent price per execution"
    )
    risk_agent_price: float = Field(
        default=0.02,
        description="Risk Guardian Agent price per assessment"
    )


class PaymentSettings(BaseModel):
    """Payment and transaction configuration"""
    timeout_seconds: int = Field(
        default=60,
        description="Payment confirmation timeout"
    )
    poll_interval_seconds: int = Field(
        default=2,
        description="Payment status polling interval"
    )
    max_poll_attempts: int = Field(
        default=30,
        description="Maximum polling attempts before timeout"
    )

    @validator("max_poll_attempts")
    def validate_max_attempts(cls, v, values):
        """Ensure total timeout is reasonable"""
        timeout = values.get("timeout_seconds", 60)
        interval = values.get("poll_interval_seconds", 2)
        max_duration = v * interval
        if max_duration > timeout + 10:
            # Allow 10s buffer
            return timeout // interval
        return v


class APISettings(BaseModel):
    """API server configuration"""
    host: str = Field(
        default="0.0.0.0",
        description="API host"
    )
    port: int = Field(
        default=8000,
        description="API port"
    )
    workers: int = Field(
        default=1,
        description="Number of worker processes"
    )
    debug: bool = Field(
        default=True,
        description="Debug mode"
    )
    cors_origins: str = Field(
        default="*",
        description="CORS allowed origins (comma-separated)"
    )
    cors_allow_credentials: bool = Field(
        default=True,
        description="CORS allow credentials"
    )

    @validator("cors_origins")
    def parse_cors_origins(cls, v):
        """Parse CORS origins"""
        if v == "*":
            return ["*"]
        return [origin.strip() for origin in v.split(",")]


class DatabaseSettings(BaseModel):
    """Database configuration (optional)"""
    database_url: Optional[str] = Field(
        default=None,
        description="PostgreSQL database URL"
    )
    redis_url: Optional[str] = Field(
        default=None,
        description="Redis URL for caching"
    )
    use_database: bool = Field(
        default=False,
        description="Whether to use database (vs in-memory)"
    )


class DeFiProtocolSettings(BaseModel):
    """DeFi protocol API configuration"""
    minswap_api_url: str = Field(
        default="https://api.minswap.org",
        description="Minswap DEX API URL"
    )
    sundaeswap_api_url: str = Field(
        default="https://api.sundaeswap.finance",
        description="SundaeSwap DEX API URL"
    )
    liqwid_api_url: str = Field(
        default="https://api.liqwid.finance",
        description="Liqwid lending protocol API URL"
    )


class SecuritySettings(BaseModel):
    """Security and authentication configuration"""
    secret_key: str = Field(
        default="CHANGE_THIS_TO_RANDOM_SECRET_KEY_IN_PRODUCTION",
        description="Secret key for JWT signing"
    )
    jwt_algorithm: str = Field(
        default="HS256",
        description="JWT algorithm"
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration time"
    )


class LoggingSettings(BaseModel):
    """Logging configuration"""
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = Field(
        default="INFO",
        description="Logging level"
    )
    log_format: Literal["json", "text"] = Field(
        default="text",
        description="Log format"
    )
    log_file: Optional[str] = Field(
        default=None,
        description="Log file path (optional)"
    )
    enable_performance_logging: bool = Field(
        default=True,
        description="Enable performance metrics logging"
    )


class Settings(BaseSettings):
    """
    Main application settings

    Loads configuration from environment variables with validation
    """

    # Core settings
    masumi: MasumiSettings = Field(default_factory=MasumiSettings)
    agent_wallets: AgentWalletSettings = Field(default_factory=AgentWalletSettings)
    cardano: CardanoSettings
    llm: LLMSettings
    agent_pricing: AgentPricingSettings = Field(default_factory=AgentPricingSettings)
    payment: PaymentSettings = Field(default_factory=PaymentSettings)
    api: APISettings = Field(default_factory=APISettings)
    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    defi_protocols: DeFiProtocolSettings = Field(default_factory=DeFiProtocolSettings)
    security: SecuritySettings = Field(default_factory=SecuritySettings)
    logging: LoggingSettings = Field(default_factory=LoggingSettings)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_nested_delimiter = "__"
        case_sensitive = False

        # Map environment variables to nested settings
        # Example: MASUMI_NODE_URL -> masumi.node_url
        fields = {
            # Masumi
            "masumi": {
                "env_prefix": "MASUMI_"
            },
            # Cardano
            "cardano": {
                "env_prefix": "CARDANO_"
            },
            # LLM
            "llm": {
                "env_prefix": "GROQ_"
            },
            # API
            "api": {
                "env_prefix": "API_"
            }
        }

    @classmethod
    def load_from_env(cls) -> "Settings":
        """
        Load settings from environment variables

        Returns:
            Settings instance with all configuration loaded
        """
        # Load .env file
        from dotenv import load_dotenv
        load_dotenv()

        # Create settings with manual mapping
        return cls(
            masumi=MasumiSettings(
                node_url=os.getenv("MASUMI_NODE_URL", "http://localhost:8080"),
                payment_service_url=os.getenv("MASUMI_PAYMENT_SERVICE_URL", "http://localhost:8080/payment"),
                registry_service_url=os.getenv("MASUMI_REGISTRY_SERVICE_URL", "http://localhost:8080/registry"),
                network=os.getenv("MASUMI_NETWORK", "preprod"),
                operational_mode=os.getenv("OPERATIONAL_MODE", "simulation"),
                enable_mip003_validation=os.getenv("ENABLE_MIP003_VALIDATION", "True").lower() == "true",
                auto_register_agents=os.getenv("AUTO_REGISTER_AGENTS", "True").lower() == "true"
            ),
            agent_wallets=AgentWalletSettings(
                market_wallet_id=os.getenv("MARKET_AGENT_WALLET_ID", "market_wallet_1"),
                market_wallet_address=os.getenv("MARKET_AGENT_WALLET_ADDRESS", "addr_test1qz..."),
                strategy_wallet_id=os.getenv("STRATEGY_AGENT_WALLET_ID", "strategy_wallet_1"),
                strategy_wallet_address=os.getenv("STRATEGY_AGENT_WALLET_ADDRESS", "addr_test1qz..."),
                risk_wallet_id=os.getenv("RISK_AGENT_WALLET_ID", "risk_wallet_1"),
                risk_wallet_address=os.getenv("RISK_AGENT_WALLET_ADDRESS", "addr_test1qz...")
            ),
            cardano=CardanoSettings(
                network=os.getenv("CARDANO_NETWORK", "preprod"),
                blockfrost_project_id=os.getenv("BLOCKFROST_PROJECT_ID", "preprodYOUR_PROJECT_ID_HERE"),
                blockfrost_api_url=os.getenv("BLOCKFROST_API_URL", "https://cardano-preprod.blockfrost.io/api/v0")
            ),
            llm=LLMSettings(
                groq_api_key=os.getenv("GROQ_API_KEY", ""),
                model=os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile"),
                temperature=float(os.getenv("GROQ_TEMPERATURE", "0.1")),
                openai_api_key=os.getenv("OPENAI_API_KEY"),
                anthropic_api_key=os.getenv("ANTHROPIC_API_KEY")
            ),
            agent_pricing=AgentPricingSettings(
                market_agent_price=float(os.getenv("MARKET_AGENT_PRICE", "0.01")),
                strategy_agent_price=float(os.getenv("STRATEGY_AGENT_PRICE", "0.05")),
                risk_agent_price=float(os.getenv("RISK_AGENT_PRICE", "0.02"))
            ),
            payment=PaymentSettings(
                timeout_seconds=int(os.getenv("PAYMENT_TIMEOUT_SECONDS", "60")),
                poll_interval_seconds=int(os.getenv("PAYMENT_POLL_INTERVAL_SECONDS", "2")),
                max_poll_attempts=int(os.getenv("PAYMENT_MAX_POLL_ATTEMPTS", "30"))
            ),
            api=APISettings(
                host=os.getenv("API_HOST", "0.0.0.0"),
                port=int(os.getenv("API_PORT", "8000")),
                workers=int(os.getenv("API_WORKERS", "1")),
                debug=os.getenv("DEBUG", "True").lower() == "true",
                cors_origins=os.getenv("CORS_ORIGINS", "*"),
                cors_allow_credentials=os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true"
            ),
            database=DatabaseSettings(
                database_url=os.getenv("DATABASE_URL"),
                redis_url=os.getenv("REDIS_URL"),
                use_database=os.getenv("USE_DATABASE", "False").lower() == "true"
            ),
            defi_protocols=DeFiProtocolSettings(
                minswap_api_url=os.getenv("MINSWAP_API_URL", "https://api.minswap.org"),
                sundaeswap_api_url=os.getenv("SUNDAESWAP_API_URL", "https://api.sundaeswap.finance"),
                liqwid_api_url=os.getenv("LIQWID_API_URL", "https://api.liqwid.finance")
            ),
            security=SecuritySettings(
                secret_key=os.getenv("SECRET_KEY", "CHANGE_THIS_TO_RANDOM_SECRET_KEY_IN_PRODUCTION"),
                jwt_algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
                access_token_expire_minutes=int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
            ),
            logging=LoggingSettings(
                log_level=os.getenv("LOG_LEVEL", "INFO"),
                log_format=os.getenv("LOG_FORMAT", "text"),
                log_file=os.getenv("LOG_FILE"),
                enable_performance_logging=os.getenv("ENABLE_PERFORMANCE_LOGGING", "True").lower() == "true"
            )
        )

    def is_production(self) -> bool:
        """Check if running in production mode"""
        return self.masumi.operational_mode == "production"

    def is_simulation(self) -> bool:
        """Check if running in simulation mode"""
        return self.masumi.operational_mode == "simulation"

    def get_agent_service_url(self, agent_type: str) -> str:
        """Get service URL for an agent type"""
        base_url = os.getenv("API_HOST", "localhost")
        port = self.api.port
        return f"http://{base_url}:{port}"


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """
    Get global settings instance (singleton)

    Returns:
        Settings instance with all configuration
    """
    global _settings

    if _settings is None:
        _settings = Settings.load_from_env()

    return _settings


# Example usage
if __name__ == "__main__":
    settings = get_settings()

    print("=" * 70)
    print("CashPilot AI Configuration")
    print("=" * 70)
    print(f"Operational Mode: {settings.masumi.operational_mode}")
    print(f"Masumi Network: {settings.masumi.network}")
    print(f"Cardano Network: {settings.cardano.network}")
    print(f"LLM Model: {settings.llm.model}")
    print(f"API Port: {settings.api.port}")
    print(f"MIP-003 Validation: {settings.masumi.enable_mip003_validation}")
    print(f"Log Level: {settings.logging.log_level}")
    print("=" * 70)
    print(f"Market Agent Price: {settings.agent_pricing.market_agent_price} ADA")
    print(f"Strategy Agent Price: {settings.agent_pricing.strategy_agent_price} ADA")
    print(f"Risk Agent Price: {settings.agent_pricing.risk_agent_price} ADA")
    print("=" * 70)

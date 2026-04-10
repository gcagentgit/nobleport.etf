"""
NoblePort Backend Configuration

Centralized settings for the NoblePort Python backend,
including Buildertrend integration parameters and database configuration.
"""

from enum import Enum
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Environment(str, Enum):
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class SyncMode(str, Enum):
    MANUAL = "manual"
    SCHEDULED = "scheduled"
    REALTIME = "realtime"


class Settings(BaseSettings):
    # Application
    app_name: str = "NoblePort Backend"
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8400
    log_level: str = "INFO"
    secret_key: str = "nobleport-dev-secret-change-in-production"

    # Database
    database_url: str = "sqlite+aiosqlite:///./nobleport.db"

    # Redis (for Celery task queue)
    redis_url: str = "redis://localhost:6379/0"

    # Buildertrend Integration
    buildertrend_base_url: str = "https://api.buildertrend.com/v1"
    buildertrend_api_key: Optional[str] = None
    buildertrend_api_secret: Optional[str] = None
    buildertrend_username: Optional[str] = None
    buildertrend_password: Optional[str] = None
    buildertrend_company_id: Optional[str] = None
    buildertrend_webhook_secret: Optional[str] = None
    buildertrend_sync_mode: SyncMode = SyncMode.SCHEDULED
    buildertrend_sync_interval_minutes: int = 15
    buildertrend_rate_limit_rpm: int = 60
    buildertrend_timeout_seconds: int = 30
    buildertrend_max_retries: int = 3

    # NoblePort ETF Bridge
    nobleport_ens_domain: str = "nobleport.eth"
    nobleport_rpc_url: str = "https://mainnet.infura.io/v3/"
    nobleport_chain_id: int = 1
    nobleport_permit_contract_address: Optional[str] = None
    nobleport_approval_contract_address: Optional[str] = None

    # Stripe Payments
    stripe_secret_key: Optional[str] = None
    stripe_webhook_secret: Optional[str] = None
    stripe_success_url: str = "http://localhost:3000/success"
    stripe_cancel_url: str = "http://localhost:3000/proposal/{proposal_id}"

    # Proposals
    proposal_expiry_days: int = 30
    deposit_required_percent: float = 25.0

    # Notifications
    sendgrid_api_key: Optional[str] = None
    notification_from_email: str = "ops@nobleport.eth"
    ops_notification_emails: list[str] = Field(default=[])
    twilio_account_sid: Optional[str] = None
    twilio_auth_token: Optional[str] = None
    twilio_from_number: Optional[str] = None

    # Stephanie.ai MCP Connection
    stephanie_mcp_endpoint: str = "http://localhost:3100/mcp"
    stephanie_api_key: Optional[str] = None

    # CORS
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8400"]
    )

    model_config = {
        "env_file": ".env",
        "env_prefix": "NOBLEPORT_",
        "case_sensitive": False,
    }


settings = Settings()

"""
Supabase Configuration for CashPilot AI
"""

import os
from supabase import create_client, Client
from typing import Optional
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)


class SupabaseConfig:
    """Supabase configuration and client management"""

    def __init__(self):
        self.url: str = os.getenv("SUPABASE_URL", "")
        self.anon_key: str = os.getenv("SUPABASE_ANON_KEY", "")
        self.service_role_key: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

        if not self.url or not self.anon_key:
            raise ValueError(
                "SUPABASE_URL and SUPABASE_ANON_KEY must be set in environment variables. "
                "See SUPABASE_SETUP.md for instructions."
            )

        self._client: Optional[Client] = None
        self._admin_client: Optional[Client] = None

    @property
    def client(self) -> Client:
        """
        Get Supabase client with anon key (for user operations)

        This client respects Row Level Security (RLS) policies
        """
        if self._client is None:
            self._client = create_client(self.url, self.anon_key)
            logger.info("✓ Supabase client initialized")
        return self._client

    @property
    def admin_client(self) -> Client:
        """
        Get Supabase client with service role key (for admin operations)

        This client BYPASSES Row Level Security (RLS) policies
        Use with caution!
        """
        if not self.service_role_key:
            raise ValueError("SUPABASE_SERVICE_ROLE_KEY not set. Required for admin operations.")

        if self._admin_client is None:
            self._admin_client = create_client(self.url, self.service_role_key)
            logger.info("✓ Supabase admin client initialized")
        return self._admin_client

    def verify_connection(self) -> bool:
        """Verify connection to Supabase"""
        try:
            # Try to query the users table
            response = self.admin_client.table("users").select("id").limit(1).execute()
            logger.info("✓ Supabase connection verified")
            return True
        except Exception as e:
            logger.error(f"✗ Supabase connection failed: {e}")
            return False


# Global Supabase configuration instance
supabase_config = SupabaseConfig()


def get_supabase_client() -> Client:
    """
    FastAPI dependency for getting Supabase client

    Usage:
        @app.get("/example")
        async def example(supabase: Client = Depends(get_supabase_client)):
            ...
    """
    return supabase_config.client


def get_supabase_admin_client() -> Client:
    """
    FastAPI dependency for getting Supabase admin client

    Usage:
        @app.post("/admin/example")
        async def admin_example(supabase: Client = Depends(get_supabase_admin_client)):
            ...
    """
    return supabase_config.admin_client

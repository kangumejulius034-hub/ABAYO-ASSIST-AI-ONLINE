"""Backward-compatible import for the shared Supabase client."""

from core.database import get_supabase_client

__all__ = ["get_supabase_client"]

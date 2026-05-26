"""
Thread-safe singleton Supabase client for logging pipeline.
Loads credentials from environment variables.
"""
import os
import logging
from pathlib import Path
from threading import Lock
from supabase import create_client, Client
from dotenv import load_dotenv

# Search for .env in the backend directory
# We know: File is in backend/services/logging/
# We need: backend/.env
base_path = Path(__file__).resolve().parent.parent.parent  # Lands in /backend/
env_path = base_path / ".env"

load_dotenv(dotenv_path=env_path)

# PFLICHT-LOGGING FÜR DAS TERMINAL (WICHTIG!)
logger = logging.getLogger(__name__)
logger.debug(
    "Supabase logging config loaded from backend env file: exists=%s url_configured=%s",
    env_path.exists(),
    bool(os.getenv("SUPABASE_URL")),
)

_schema_check_disabled_notice_emitted = False


class SupabaseClientSingleton:
    """
    Thread-safe singleton for Supabase client.
    Ensures only one client instance exists across the application.
    """
    _instance: Client = None
    _lock: Lock = Lock()
    _initialized: bool = False

    def __new__(cls) -> Client:
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    supabase_url = os.getenv("SUPABASE_URL")
                    supabase_key = os.getenv("SUPABASE_KEY")

                    if not supabase_url:
                        raise ValueError("SUPABASE_URL environment variable is not set")
                    if not supabase_key:
                        raise ValueError("SUPABASE_KEY environment variable is not set")

                    cls._instance = create_client(supabase_url, supabase_key)
                    cls._initialized = True

        return cls._instance

    @classmethod
    def is_initialized(cls) -> bool:
        """Check if the singleton has been initialized."""
        return cls._initialized

    @classmethod
    def reset(cls) -> None:
        """
        Reset the singleton instance.
        Primarily used for testing purposes.
        """
        with cls._lock:
            cls._instance = None
            cls._initialized = False


def get_supabase_client() -> Client:
    """
    Get the Supabase client instance.
    
    Returns:
        Client: The Supabase client singleton instance.
        
    Raises:
        ValueError: If SUPABASE_URL or SUPABASE_KEY environment variables are not set.
    """
    return SupabaseClientSingleton()


def ensure_logging_schema() -> None:
    """
    Ensure that the logs_raw table has the required schema for logging pipeline.
    
    Checks if the trace_id column exists in logs_raw table via information_schema.
    If missing, executes ALTER TABLE to add the column and create an index.
    
    This function should be called during application startup to ensure schema consistency.
    
    Raises:
        Exception: If schema validation or migration fails.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    global _schema_check_disabled_notice_emitted
    try:
        client = get_supabase_client()
        
        # Check if trace_id column exists in logs_raw
        check_query = """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name = 'logs_raw'
            AND column_name = 'trace_id'
            AND table_schema = 'public'
        """
        
        result = client.rpc('exec_sql', {'sql': check_query}).execute()
        
        # If result is empty or no data, column doesn't exist
        if not result.data or len(result.data) == 0:
            logger.warning("Schema validation: trace_id column missing in logs_raw. Adding column...")
            
            # Add trace_id column
            alter_query = """
                ALTER TABLE logs_raw
                ADD COLUMN IF NOT EXISTS trace_id TEXT;
            """
            client.rpc('exec_sql', {'sql': alter_query}).execute()
            
            # Create index on trace_id for performance
            index_query = """
                CREATE INDEX IF NOT EXISTS idx_logs_raw_trace_id
                ON logs_raw(trace_id);
            """
            client.rpc('exec_sql', {'sql': index_query}).execute()
            
            logger.info("Schema migration completed: trace_id column added to logs_raw")
        else:
            logger.info("Schema validation: trace_id column exists in logs_raw")
            
    except Exception as e:
        msg = str(e)
        # Some Supabase deployments do not expose custom SQL RPC helpers like public.exec_sql.
        # In that case, skip schema auto-migration quietly to avoid repeated error spam.
        if "Could not find the function public.exec_sql" in msg or "PGRST202" in msg:
            if not _schema_check_disabled_notice_emitted:
                logger.warning(
                    "Schema validation skipped: RPC helper 'public.exec_sql' not available in this Supabase project."
                )
                _schema_check_disabled_notice_emitted = True
            else:
                logger.debug("Schema validation skipped (exec_sql unavailable).")
            return
        logger.error(f"Schema validation failed: {e}")
        # Don't raise - allow application to start even if schema check fails
        # The logging pipeline will handle schema errors gracefully
